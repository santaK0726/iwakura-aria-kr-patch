"""PNG image boundary and MAGES PACK sprite-table preservation.

Pillow reads pixels but discards bytes after IEND. Those bytes can be required
game data, so every edited PNG must retain its immutable source suffix.
"""
import hashlib,struct,zlib
SIGNATURE=b'\x89PNG\r\n\x1a\n'
def sha(data):return hashlib.sha256(data).hexdigest()
def inspect_png(data):
    assert data.startswith(SIGNATURE),'Not PNG'
    p=8;size=None
    while p+12<=len(data):
        length=struct.unpack_from('>I',data,p)[0];tag=data[p+4:p+8];end=p+12+length
        assert end<=len(data),'Truncated PNG chunk'
        body=data[p+8:p+8+length];crc=struct.unpack_from('>I',data,p+8+length)[0]
        assert zlib.crc32(tag+body)&0xffffffff==crc,'PNG chunk CRC mismatch'
        if tag==b'IHDR':
            assert p==8 and length==13;size=struct.unpack_from('>II',body)
        p=end
        if tag==b'IEND':assert length==0;break
    else:raise ValueError('Missing PNG IEND')
    assert size is not None
    suffix=data[p:];records=[]
    if suffix:
        assert suffix.endswith(b'PACK') and len(suffix)>=8,'Unknown PNG suffix; investigate before rebuilding'
        count=struct.unpack_from('<I',suffix,len(suffix)-8)[0]
        assert len(suffix)==count*28+8,'Invalid PACK record count'
        for i in range(count):
            row=struct.unpack_from('<7i',suffix,i*28)
            ident,dx,dy,sx,sy,w,h=row
            assert ident==i and min(sx,sy)>=0 and min(w,h)>0
            assert sx+w<=size[0] and sy+h<=size[1],('PACK source rectangle out of bounds',i,row,size)
            records.append(row)
    return dict(image_end=p,size=list(size),suffix=suffix,suffix_size=len(suffix),suffix_sha256=sha(suffix),pack_records=records)
def preserve_png_suffix(encoded,source):
    original=inspect_png(source);candidate=inspect_png(encoded)
    assert not candidate['suffix'] or candidate['suffix']==original['suffix'],'Conflicting PNG suffix'
    if original['suffix']:assert candidate['size']==original['size'],'Cannot resize a PACK atlas without remapping its table'
    result=encoded[:candidate['image_end']]+original['suffix'];readback=inspect_png(result)
    assert readback['suffix']==original['suffix'] and readback['pack_records']==original['pack_records']
    return result
def suffix_report(data):
    r=inspect_png(data)
    return dict(png_suffix_bytes=r['suffix_size'],png_suffix_sha256=r['suffix_sha256'],pack_record_count=len(r['pack_records']))
