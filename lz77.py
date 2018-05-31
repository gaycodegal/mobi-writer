def CHAR(x):
    return x#(x)-256 if ( (x) > 127 ) else (x)


def cpalmdoc_memcmp(a, sa, b, sb, length):
    for i in range(length):#(i = 0; i < len; i++)
        if (a[sa + i] != b[sb + i]):
            return False
    return True;


def cpalmdoc_rfind(data, pos, chunk_length):
    for i in range(pos-chunk_length, -1, -1):# (i = pos - chunk_length; i > -1; i--)
        if (cpalmdoc_memcmp(data,i, data,pos, chunk_length)):
            return i;
    return pos;



def cpalmdoc_do_compress(b, output):
    #Py_ssize_t i = 0, j, chunk_len, dist;
    #unsigned int compound;
    #Byte c, n;
    found = False
    temp = [0] * 8
    tlen = 0
    i = 0
    outi = 0
    while (i < len(b)):# {
        c = b[i]
        #do repeats
        if ( i > 10 and (len(b) - i) > 10):# {
            found = False;
            for chunk_len in range(10, 2, -1):#(chunk_len = 10; chunk_len > 2; chunk_len--):# {
                j = cpalmdoc_rfind(b, i, chunk_len);
                dist = i - j;
                if (j < i and dist <= 2047):# {
                    found = True;
                    compound = ((dist << 3) + chunk_len - 3)
                    output[outi] = CHAR(0x80 + (compound >> 8 ));
                    outi += 1;
                    output[outi] = CHAR(compound & 0xFF);
                    outi += 1;
                    i += chunk_len;
                    break;
                #}
            #}
            if (found): continue;
        #}
        
        #write single character
        i+=1;
        if (c == 32 and i < len(b)):# {
            n = b[i];
            if ( n >= 0x40 and n <= 0x7F):# {
                output[outi] = CHAR(n^0x80);
                outi += 1;
                i+=1;
                continue;
            #}
        #}
        if (c == 0 or (c > 8 and c < 0x80)):
            outi += 1; output[outi - 1] = CHAR(c);
        else:# { // Write binary data
            j = i;
            temp[0] = c; tlen = 1;
            while (j < len(b) and tlen < 8):# {
                c = b[j];
                if (c == 0 or (c > 8 and c < 0x80)):
                    break
                temp[tlen] = c;
                j+=1;
                tlen+=1
            #}
            i += tlen - 1;
            output[outi] = tlen;
            outi += 1;
            for k in range(tlen):
                output[outi] = temp[k];
                outi += 1;
        #}
    #}
    return outi
#}

def encode(_input):# {
    input_len = len(_input)
    b = [0]*input_len
    
    #// Map chars to bytes
    for j in range(input_len):
        b[j] =  _input[j]+256 if (_input[j] < 0) else  _input[j];
    #// Make the output buffer larger than the input as sometimes
    #// compression results in a larger block
    output = [0] * int(1.25 * len(b))
    j = cpalmdoc_do_compress(b, output);
    if ( j == 0):
        raise "ehhh"
    return bytes(output[:j]);

def main():
    with open("test.bin", "wb") as f:
        a = encode(b"the shiny shoe is never short of a shedding cat. :3")
        print(a)
        f.write(a)

if __name__ == "__main__":
    main()
