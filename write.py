import time
import struct
import sys
from pprint import pprint
from lz77 import encode
def printZIP(a, b):
    for item in zip(a, b):
        print(item)

def parsePalmHeader(f):
    return readStruct(f,'>HHIHHHH', [
        "compression",
        "unused",
        "text_length",
        "record_count",
        "record_size",
        "encryption_type",
        "unknown"
    ])

def parseMobiHeader(f, records):
    offset = f.tell()
    header = readStruct(f,'> IIII II 40s III IIIII IIII I 36s IIII 8s HHIIIII 8sI IIIII',[
        "identifier",
        "header_length",
        "Mobi type",
        "text Encoding",

      "Unique-ID",
        "Generator version",

        None, #"-Reserved",

      "First Non-book index",
        "Full Name Offset",
        "Full Name Length",

      "Language",
        "Input Language",
        "Output Language",
        "Format version",
        "First Image index",

      "First Huff Record",
        "Huff Record Count",
        "First DATP Record",
        "DATP Record Count",

      "EXTHflags",

        None, #"-36 unknown bytes, if Mobi is long enough",

      "DRM Offset",
        "DRM Count",
        "DRM Size",
        "DRM Flags",

        "Zero", #"-Usually Zeros, unknown 8 bytes",

        "First Content",
        "Last Content",
        None, #"-Unknown",
        "FCIS record",
        None, #"-Unknown",
        "FLIS record",
        None, #"-Unknown"
        
        None, #"-Unknown 0x0000000000000000"
        None, #"-Unknown 0xFFFFFFFF"
        
        None, #First Compilation data section count	Use 0x00000000
        None, #Number of Compilation data sections	Use 0xFFFFFFFF.
        None, #Unknown	Use 0xFFFFFFFF.
        None, #Extra Record Data Flags
        "INDX_offset"#INDX Record Offset if not 0xFFFFFFFF
        #more garbage
    ])

    f.seek(records[0]["offset"] + header["Full Name Offset"])
    header["name"] = f.read(header["Full Name Length"])
    f.seek(offset + header["header_length"])
    pprint(header)
    return header
def readStruct(f, fmt, fields, slen = None):
    if slen == None:
        slen = struct.calcsize(fmt)
        data = struct.unpack(fmt, f.read(slen))
    return {key:value for key,value in
            zip(fields, data)
            if key != None
    }


def parseEXTHHeader(f):
    header = readStruct(f, '>4sII', [
        'id',
        'length',
        '#records'
    ])
    print("exth", header)

    records = [0] * header["#records"]
    fmt = ">II"
    print(header["#records"])
    for r in range(header['#records']):
        rec = readStruct(f, fmt, ["type", "length"])
        print(rec)
        rec["length"] -= 8
        rec["data"] = f.read(rec["length"])
        records[r] = rec

    header["records"] = records
    return header

def test():
    with open(sys.argv[2] if len(sys.argv) >= 3 else "Test.mobi", "rb") as f:
        index = 0
        glob_header = readStruct(f, '>32shhIIIIII4s4sIIH', [
            "name",
            "attributes",
            "version",
            "created",
            "modified",
            "backup",
            "modnum",
            "appInfoId",
            "sortInfoID",
            "type",
            "creator",
            "uniqueIDseed",
            "nextRecordListID",
            "#records"
        ])
        
        print(glob_header)

    
        ## get records
        fmt = ">II"
        fields = [
            "offset",
            "UID",
        ]
        records = [0] * glob_header["#records"]
        for r in range(glob_header["#records"]):
            rec = readStruct(f, fmt, fields)
            rec["attr"] = (rec['UID'] & 0xFF000000) >> 24
            rec["UID"] = rec["UID"] & 0xFFFFFF
            records[r] = rec
            print(records[r])
            
        #now parse palmdoc
        f.seek(records[0]["offset"])
        palm_header = parsePalmHeader(f)
        print(palm_header)
        
        #now mobi
        mobi_header = parseMobiHeader(f, records)
        if mobi_header["EXTHflags"] & 0x40:
            exth_header = parseEXTHHeader(f)
            pprint(exth_header)

def mobiheaderlen():
    return struct.calcsize('> 4sIII II 40s III IIIII IIII I 36s IIII 8s HHIIIII 8sI IIII I 20s I') #mobi + name

def nameOffset(exthsize):
    return struct.calcsize('>HHIHHHH') + mobiheaderlen() + exthsize

def sizeofHeader(name, recordlen, exthsize):
    return struct.calcsize('>32shhIIIIII4s4sIIH') + (struct.calcsize(">II") * recordlen) + nameOffset(exthsize) + len(name)

def sizeofGlobHeader(recordlen):
    return struct.calcsize('>32shhIIIIII4s4sIIH')+ (struct.calcsize(">II") * recordlen) #records

def sizeofExthHeader(data):
    e = struct.calcsize('>4sII') + (len(data) * struct.calcsize("II")) + sum([len(rec['data']) for rec in data])
    pad = 4 - (e % 4)
    return e + pad, pad
    
def generateMobi(name, text):
    exth = [{'data': b'Test', 'type': 503},
            {'data': b'en', 'type': 524},
            {'data': b'My Author', 'type': 100},
            {'data': b'calibre (3.16.0) [https://calibre-ebook.com]',
             'type': 108},
            {'data': b'443467fb-212b-4817-8519-e9009343355d',
             'type': 113},
            {'data': b'calibre:443467fb-212b-4817-8519-e9009343355d',
             'type': 112},
            {'data': b'EBOK', 'type': 501},
            {'data': b'2018-05-30T21:40:16.296448+00:00',
             'type': 106},
            {'data': b'\x00\x00\x00\xc9', 'type': 204},
            {'data': b'\x00\x00\x00\x01', 'type': 205},
            {'data': b'\x00\x00\x00\x02', 'type': 206},
            {'data': b'\x00\x00\x82\x1b', 'type': 207},
            {'data': b'\x00\x00\x00\x19', 'type': 116},
            {'data': b'\x00\x00\x00\x00', 'type': 131}]
    exthsize, exthpad = sizeofExthHeader(exth)
    
    nmagicrecords = 4 # '\0\0', flis, fcis, crlf
    with open(name + b".mobi", "wb") as f:
        padded_name = name + b"\0\0" + ((len(name) + 2) % 4 * b"\0")
        record_size = 4096
        text_length = len(text)
        #glob_header
        modtext = text_length % record_size
        recordlen = (text_length // record_size) + (0 if (modtext == 0) else 1) + 1 + nmagicrecords #plus one for palm meta record plus n magic records
        attributes = 0
        version = 0
        created = int(time.time())
        modified = created
        backup = 0
        modnum = 0
        appInfoId = 0
        sortInfoId = 0
        atype = b"BOOK"
        creator = b"MOBI"
        uniqueIDseed = recordlen
        nextRecordListID = 0
        
        shortname = name[:31]
        shortname = shortname + b"\0" * (32 - len(shortname))
        f.write(struct.pack('>32shhIIIIII4s4sIIH',
                            shortname,
                            attributes,
                            version,
                            created,
                            modified,
                            backup,
                            modnum,
                            appInfoId,
                            sortInfoId,
                            atype,
                            creator,
                            uniqueIDseed,
                            nextRecordListID,
                            recordlen
        ))
        hsize = sizeofHeader(padded_name, recordlen, exthsize)
        f.write(struct.pack('>II', sizeofGlobHeader(recordlen), 0)) # meta record
        print(hsize)
        textsize = 0
        textsnips = []
        for r in range(recordlen - 1 - nmagicrecords):
            print("wrote record", hsize + (record_size * r), r + 1)
            textsnips.append(encode(text[r * 4096: (r+1) * 4096]))
            f.write(struct.pack('>II', hsize + textsize, r + 1))
            textsize += len(textsnips[-1])
        offset = hsize + textsize
        f.write(struct.pack('>II', offset, recordlen - 4)) # double null
        f.write(struct.pack('>II', offset + 2, recordlen - 3)) # FLIS
        f.write(struct.pack('>II', offset + 36 + 2, recordlen - 2)) # FCIS
        f.write(struct.pack('>II', offset + 36 + 44 + 2, recordlen - 1)) # CRLF
        # palm

            
        compression = 2 # no compression
        unused = 0
        encryption_type = 0 # none
        unknown = 0 #usu zero
        f.write(struct.pack('>HHIHHHH',
                            compression,
                            unused,
                            len(text),
                            recordlen - nmagicrecords,
                            record_size,
                            encryption_type,
                            unknown))
        
        # mobi
        mobitype = 2 # book
        encoding = 65001 #utf-8
        genver = 6
        nameoffset =  nameOffset(exthsize)
        print("recordlen", recordlen)
        f.write(struct.pack('> 4sIII II 40s III IIIII IIII I 36s IIII 8s HHIIIII 8sI IIII I 20s I',
                            b"MOBI",
                            mobiheaderlen(),
                            mobitype,
                            encoding,
                            
                            recordlen, # a uid
                            genver,
                            
                            (struct.pack(">I", 0xFFFFFFFF) * 10),
                            
                            recordlen - nmagicrecords + 1, #first non book (flis)
                            nameoffset,
                            len(name),
                            
                            9, #english
                            9, #english in
                            9, #english out
                            genver,
                            0xFFFFFFFF, # first image index
                            
                            0xFFFFFFFF,
                            0,#huff count
                            0,#off
                            0,#length
                            
                            0x40, #exth
                            
                            ((struct.pack(">I", 0xFFFFFFFF) * 36)),

                            0xFFFFFFFF,#drm off
                            0,#drm count
                            0,#drm size
                            0, #drm flags

                            b"\0" * 8,

                            1,#first text record
                            recordlen - nmagicrecords - 1,#last content
                            1,#unknown
                            recordlen - nmagicrecords + 2,#fcis
                            1, #"-Unknown",
                            recordlen - nmagicrecords + 1,#"FLIS record",
                            1, #"-Unknown"
                            
                            b"\0" * 8, #"-Unknown 0x0000000000000000"
                            0xFFFFFFFF, #"-Unknown 0xFFFFFFFF"
                            
                            0, #First Compilation data section count	Use 0x00000000
                            0xFFFFFFFF, #Number of Compilation data sections	Use 0xFFFFFFFF.
                            0xFFFFFFFF, #Unknown	Use 0xFFFFFFFF.
                            0, #Extra Record Data Flags
                            0xFFFFFFFF,#INDX Record Offset if not 0xFFFFFFFF
                            ((struct.pack(">I", 0xFFFFFFFF) * 5)),
                            0
                            
        ))

        # EXTH Header
        f.write(struct.pack("> 4sII",
                b"EXTH",
                exthsize,
                len(exth)
                ))

        for data in exth:
            f.write(struct.pack("> II", data["type"], len(data["data"]) + struct.calcsize(">II")))
            f.write(data["data"])
        f.write(exthpad * b"\0")
        f.write(padded_name)
        for snip in textsnips:
            print("wrote", (snip), "at", f.tell())
            #print("wrote", text[r*record_size:(r+1)*record_size])
            f.write(snip)
        #f.write(b" " * (record_size - modtext))
        f.write(b"\0\0")
        f.write(struct.pack("> 4sIHH IIHH III", b"FLIS", 8, 65, 0,
                            0, 0xFFFFFFFF, 1, 3,
                            3, 1, 0xFFFFFFFF))
        f.write(struct.pack("> 4sIII IIII IHHI", b"FCIS", 20,16,1,
                            0, text_length, 0, 32,
                            8, 1, 1, 0))
        f.write(b"\xe9\x8e\x0d\x0a")

if len(sys.argv) >= 2 and sys.argv[1] == "test":
    test()
else:
    generateMobi(b"Test", b'<html><head><guide></guide></head><body><div><br/> <br/>Testing Testing 1 2 3<br/></div></body></html>')
