# Mobi Writer

A Python3 script that writes files to the mobi file format. Works, but still in development. Generated content at present is viewable in calibre, but I have yet to successfully open it on an actual ereader. I did convert it through calibre into something that works on an e-reader, but would like to be able to generate it myself.

Development stopping for the moment, I'm missing some critical piece of info that lets calibre write for e-reader devices but not me. However, I learned about how ebooks work, and can probably find my missing piece should I decide it worth it in the future. And hey it can be read by calibre, so that's a win at least.

The lz77 encoding algorithm is just a python version of calibre's lz77 python-c file.

## Files

- Test.mobi - latest file generated by write.py
- Test2.mobi - converted via calibre into something that works

## Running

	python writer.py
	
This will generate a file `Test.mobi` which can be viewed with software like calibre. The contents of the file will look like

	Testing Testing 1 2 3
	
## Steps

- writes main file table
- writes record zero
    - writes palm header
    - writes mobi header
    - writes name, padded
- writes contents
- writes 2-null byte record
- writes FLIS record
- writes FCIS record
- writes CRLF record
