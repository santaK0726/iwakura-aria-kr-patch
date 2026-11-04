"""Source-bound MSB, MPK and image delta reconstruction. No retail assets."""
if not __debug__:
    raise RuntimeError("Run without Python -O/-OO; integrity checks are required")
import argparse,hashlib,io,json,os,struct,zlib,zipfile
from pathlib import Path
from PIL import Image
from png_container import preserve_png_suffix,inspect_png

def sha(data):return hashlib.sha256(data).hexdigest()
def index(data):
    assert data[:8]==b'MPK\0\0\0\2\0','Wrong MPK version'
    count=struct.unpack_from('<I',data,8)[0];end=0x40+count*0x100;assert end<=len(data)
    rows=[];seen=set()
    for i in range(count):
        at=0x40+i*0x100;flags,ident,offset,packed,unpacked=struct.unpack_from('<IIQQQ',data,at)
        name=data[at+32:at+256].split(b'\0')[0].decode('utf-8')
        assert name not in seen and name not in {'','.','..'} and '/' not in name and '\\' not in name
        assert flags==0 and packed==unpacked and offset>=end and offset+packed<=len(data)
        seen.add(name);rows.append(dict(index=i,name=name,id=ident,offset=offset,size=packed))
    spans=sorted((r['offset'],r['offset']+r['size']) for r in rows)
    assert all(x[1]<=y[0] for x,y in zip(spans,spans[1:]))
    return rows

def msb(data):
    assert data[:4]==b'MES\0';version,count,start=struct.unpack_from('<III',data,4)
    assert version==1 and start==16+count*8 and start<=len(data)
    table=[struct.unpack_from('<II',data,16+i*8) for i in range(count)];offsets=[start+r[1] for r in table]+[len(data)]
    assert (not count or offsets[0]==start) and all(x<=y for x,y in zip(offsets,offsets[1:]))
    return data[:16],table,[data[offsets[i]:offsets[i+1]] for i in range(count)]

def msb_write(header,table,strings):
    out=bytearray(header);offset=0
    for (ident,_),raw in zip(table,strings):out.extend(struct.pack('<II',ident,offset));offset+=len(raw)
    return bytes(out)+b''.join(strings)

def pack(original,replacements):
    rows=index(original);assert set(replacements)<=set(r['name'] for r in rows);out=bytearray(original);writes=[]
    for r in rows:
        if r['name'] not in replacements:continue
        raw=replacements[r['name']];assert raw!=original[r['offset']:r['offset']+r['size']]
        out.extend(b'\0'*(-len(out)%0x800));offset=len(out);out.extend(raw)
        at=0x40+r['index']*0x100+8;value=struct.pack('<QQQ',offset,len(raw),len(raw));out[at:at+24]=value
        writes.append(dict(member=r['name'],index_offset=at,payload_offset=offset,payload_size=len(raw),payload_sha256=sha(raw)))
    protected=bytearray(out[:len(original)])
    for w in writes:
        at=w['index_offset'];protected[at:at+24]=original[at:at+24]
    assert protected==original,'Protected MPK prefix differs'
    old={r['name']:r for r in rows}
    for r in index(out):
        prior=old[r['name']];expected=replacements.get(r['name'],original[prior['offset']:prior['offset']+prior['size']])
        assert out[r['offset']:r['offset']+r['size']]==expected
    return bytes(out),writes

def xor_bytes(left,right):
    assert len(left)==len(right)
    try:
        import numpy as np
        return np.bitwise_xor(np.frombuffer(left,dtype='uint8'),np.frombuffer(right,dtype='uint8')).tobytes()
    except ImportError:return bytes(a^b for a,b in zip(left,right))

_PAYLOAD_ARCHIVES={}
def payload(bundle,record):
    path=(bundle/record['file']).resolve();assert bundle.resolve() in path.parents
    archive=bundle/'payloads.zip'
    if archive.exists():
        key=str(archive.resolve())
        if key not in _PAYLOAD_ARCHIVES:_PAYLOAD_ARCHIVES[key]=zipfile.ZipFile(archive,'r')
        packed=_PAYLOAD_ARCHIVES[key].read(record['file'])
    else:packed=path.read_bytes()
    assert sha(packed)==record['sha256'],'Delta payload changed'
    raw=zlib.decompress(packed);assert len(raw)==record['raw_size'] and sha(raw)==record['raw_sha256']
    return raw

def reconstruct(original,recipe,bundle):
    assert sha(original)==recipe['source_sha256'],recipe['member']+' source mismatch'
    kind=recipe['kind']
    if kind=='msb-records':
        header,table,strings=msb(original);assert len(strings)==recipe['record_count'];seen=set()
        for change in recipe['changes']:
            i=change['index'];assert i not in seen and table[i][0]==change['record_id'];seen.add(i)
            assert sha(strings[i])==change['source_raw_sha256'];strings[i]=payload(bundle,change['payload'])
        built=msb_write(header,table,strings);rh,rt,rs=msb(built)
        assert rh==header and [x[0] for x in rt]==[x[0] for x in table] and rs==strings
    elif kind=='prefix-patches-and-append':
        out=bytearray(original);allowed=set()
        for patch in recipe['patches']:
            at=patch['offset'];old=bytes.fromhex(patch['expected']);new=bytes.fromhex(patch['replacement']);assert len(old)==len(new)==4
            assert out[at:at+4]==old and not allowed.intersection(range(at,at+4));allowed.update(range(at,at+4));out[at:at+4]=new
        assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(original,out)))
        out.extend(payload(bundle,recipe['append']));built=bytes(out)
    elif kind=='append':built=original+payload(bundle,recipe['append'])
    elif kind=='pixel-xor':
        source=Image.open(io.BytesIO(original)).convert(recipe['mode']);assert list(source.size)==recipe['source_size']
        canvas=Image.new(recipe['mode'],tuple(recipe['size']),0);canvas.paste(source,(0,0))
        raw=xor_bytes(canvas.tobytes(),payload(bundle,recipe['xor']));assert sha(raw)==recipe['pixels_sha256']
        image=Image.frombytes(recipe['mode'],tuple(recipe['size']),raw);stream=io.BytesIO()
        image.save(stream,format=recipe['format'],**recipe.get('save_kwargs',{}));built=stream.getvalue()
        if recipe.get('png_suffix_policy')=='preserve-source':
            info=inspect_png(original)
            assert info['suffix_sha256']==recipe['source_png_suffix_sha256'] and info['suffix_size']==recipe['source_png_suffix_size']
            built=preserve_png_suffix(built,original)
        rb=Image.open(io.BytesIO(built)).convert(recipe['mode']);assert rb.size==image.size and rb.tobytes()==raw
    else:raise ValueError('Unknown delta recipe: '+kind)
    assert len(built)==recipe['output_size'] and sha(built)==recipe['output_sha256'],recipe['member']+' output encoding mismatch; use the recorded Pillow/libwebp runtime'
    return built
