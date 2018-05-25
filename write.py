import time
import struct
import sys
from pprint import pprint
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
    header = readStruct(f,'> IIII II 40s III IIIII IIII I 36s IIII 8s HHIIIII LI IIIII',[
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

        None, #"-Usually Zeros, unknown 8 bytes",

        None, #"-Unknown",
        "Last Image Record",
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
    header = readStruct(f, '>III', [
        'id',
        'length',
        '#records'
    ])

    records = [0] * header["#records"]
    fmt = ">II"
    print(header["#records"])
    for r in range(header['#records']):
        rec = readStruct(f, fmt, ["type", "length"])
        rec["length"] -= 8
        rec["data"] = f.read(rec["length"])
        records[r] = rec

    header["records"] = records
    return header

def test():
    with open("the_end_is_nigh.mobi", "rb") as f:
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
            print(records[0])
            
        #now parse palmdoc
        f.seek(records[0]["offset"])
        palm_header = parsePalmHeader(f)
        print(palm_header)
        
        #now mobi
        mobi_header = parseMobiHeader(f, records)
        if mobi_header["EXTHflags"] & 0x40:
            exth_header = parseEXTHHeader(f)
            pprint(exth_header)

def mobiheaderlen(name):
    return struct.calcsize('>HHIHHHH') + struct.calcsize('> 4sIII II 40s III IIIII IIII I 36s IIII L HHIIIII LI IIII I 20s I') + len(name) #mobi + name

def sizeofHeader(name, recordlen):
    return struct.calcsize('>32shhIIIIII4s4sIIH') + (struct.calcsize(">II") * recordlen) + mobiheaderlen(name)

def sizeofGlobHeader(recordlen):
    return struct.calcsize('>32shhIIIIII4s4sIIH')+ (struct.calcsize(">II") * recordlen) #records

    
def generateMobi(name, text):
    with open(name + b".mobi", "wb") as f:
        record_size = 4096
        text_length = len(text)
        #glob_header
        modtext = text_length % record_size
        recordlen = (text_length // record_size) + (0 if (modtext == 0) else 1) + 1 + 1 #plus one for palm meta record plus one for empty record
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
        
        shortname = name[:32]
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
        hsize = sizeofHeader(name, recordlen)
        f.write(struct.pack('>II', sizeofGlobHeader(recordlen), 0)) # meta record
        print(hsize)
        for r in range(recordlen - 2):
            f.write(struct.pack('>II', hsize + (record_size * r), r + 1))
        f.write(struct.pack('>II', hsize + record_size * (recordlen - 3) +  (record_size if modtext == 0 else modtext), recordlen - 1))
        # palm

            
        compression = 1 # no compression
        unused = 0
        encryption_type = 0 # none
        unknown = 0 #usu zero
        f.write(struct.pack('>HHIHHHH',
                            compression,
                            unused,
                            len(text),
                            recordlen,
                            record_size,
                            encryption_type,
                            unknown))

        # mobi
        mobitype = 2 # book
        encoding = 65001 #utf-8
        genver = 6
        nameoffset =  mobiheaderlen(name) - len(name)
        print("recordlen", recordlen)
        f.write(struct.pack('> 4sIII II 40s III IIIII IIII I 36s IIII L HHIIIII LI IIII I 20s I',
                            b"MOBI",
                            mobiheaderlen(name),
                            mobitype,
                            encoding,
                            
                            recordlen, # a uid
                            genver,
                            
                            (struct.pack(">I", 0xFFFFFFFF) * 10),
                            
                            recordlen, #last empty record
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
                            
                            0, #exth
                            
                            ((struct.pack(">I", 0xFFFFFFFF) * 36)),

                            0xFFFFFFFF,#drm off
                            0,#drm count
                            0,#drm size
                            0, #drm flags

                            0,

                            1,#first text record
                            recordlen,#last content
                            1,#unknown
                            0,#fcis
                            1, #"-Unknown",
                            0,#"FLIS record",
                            1, #"-Unknown"
                            
                            0, #"-Unknown 0x0000000000000000"
                            0xFFFFFFFF, #"-Unknown 0xFFFFFFFF"
                            
                            0, #First Compilation data section count	Use 0x00000000
                            0xFFFFFFFF, #Number of Compilation data sections	Use 0xFFFFFFFF.
                            0xFFFFFFFF, #Unknown	Use 0xFFFFFFFF.
                            0, #Extra Record Data Flags
                            0xFFFFFFFF,#INDX Record Offset if not 0xFFFFFFFF
                            ((struct.pack(">I", 0xFFFFFFFF) * 5)),
                            0
                            
        ))
        f.write(name)
        for r in range(recordlen - 2):
            print("wrote", text[r*record_size:(r+1)*record_size])
            f.write(text[r*record_size:(r+1)*record_size])
        f.write(b"\xe9\x8e\x0d\x0a")
#test()       
generateMobi(b"Test", b'<html><head><guide></guide></head><body><div><br/> <br/>Testing Testing 1 2 3<br/></div></body></html>')
