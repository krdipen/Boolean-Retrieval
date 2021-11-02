import os, re, sys, snappy
sys.path.append('.')
from bs4 import BeautifulSoup
from stemmer import PorterStemmer

class compress:

    def c0(self, index):
        index = str(index) + ' '
        bytes = ''
        for ch in index:
            byte = bin(ord(ch))[2:]
            byte = '0' * (8-len(byte)) + byte
            bytes += byte
        return bytes

    def c1(self, index):
        index = bin(index)[2:]
        bytes = ''
        for i in range(0, len(index), 7):
            byte = index[max(0,len(index)-i-7):len(index)-i]
            byte = '0' * (7-len(byte)) + byte
            bytes = '0' + byte + bytes if i==0 else '1' + byte + bytes
        return bytes
        
    def c2(self, index):
        x = index
        bx = bin(x)[2:]
        lx = len(bx)
        blx = bin(lx)[2:]
        llx = len(blx)
        bytes = ''
        for i in range(1, llx):
            bytes += '1'
        bytes += '0'
        for i in range(1, llx):
            bytes += blx[i]
        for i in range(1, lx):
            bytes += bx[i]
        return bytes
    
    def c3(self, index):
        index = snappy.compress(index.encode('ascii'))
        bytes = ''
        for ch in index:
            byte = bin(ch)[2:]
            byte = '0' * (8-len(byte)) + byte
            bytes += byte
        return bytes

    def c4(self, index, k):
        b = 2 ** k
        q = (index-1) // b
        r = (index-1) % b
        br = bin(r)[2:]
        br = '0' * (k-len(br)) + br
        bytes = ''
        for i in range(0, q):
            bytes += '1'
        bytes += '0'
        for ch in br:
            bytes += ch
        return bytes

    def c5(self, index, k):
        index = bin(index)[2:]
        bytes = '0'*(k-len(index)) + index
        return bytes

def main():

    file = open(sys.argv[5], 'r')
    tags = file.read().strip().split()
    file.close()
    file = open(sys.argv[3], 'r')
    stopwords = list(map(str.lower, file.read().strip().split()))
    file.close()
    docids = []
    invidx = {}
    os.mkdir('invidx')
    ps = PorterStemmer()
    collection_path = sys.argv[1]
    for filename in os.listdir(collection_path):
        try:
            file = open(collection_path + '/' + filename, 'r')
        except:
            for file in invidx:
                invidx[file].close()
            invidx = {}
            file = open(collection_path + '/' + filename, 'r')
        html = BeautifulSoup(file.read(), 'lxml')
        file.close()
        docs = html.find_all('doc')
        for doc in docs:
            words = set()
            docid = doc.find(tags[0].lower()).text.strip()
            docids.append(docid)
            for tag in tags[1:]:
                text = ''
                texts = doc.find_all(tag.lower())
                for text in texts:
                    text = text.text.strip()
                    tokens = re.split('[.,:;\\\\/\n\t\s\r\'\"\(\)\[\]\{\}]', text)
                    tokens = filter(lambda x : True if len(x) > 0 else False, tokens)
                    terms = [ps.stem(token, 0, len(token)-1).lower() for token in tokens]
                    words.update([term for term in terms if term not in stopwords])
            for word in words:
                if word not in invidx:
                    try:
                        invidx[word] = open('invidx/' + word, 'a')
                    except:
                        for file in invidx:
                            invidx[file].close()
                        invidx = {}
                        try:
                            invidx[word] = open('invidx/' + word, 'a')
                        except:
                            continue
                invidx[word].write(f'{len(docids)}\n')
    for file in invidx:
        invidx[file].close()
    invidx = {}

    idxfile = open(sys.argv[2] + '.idx', 'wb')
    dictfile = open(sys.argv[2] + '.dict', 'w')
    compression = sys.argv[4]
    if compression in ['1', '2', '3', '4']:
        for word in os.listdir('invidx'):
            file = open('invidx/' + word, 'r')
            plist = list(map(int, file.read().strip().split()))
            file.close()
            file = open('invidx/' + word, 'w')
            file.write(f'{plist[0]}\n')
            for i in range(1, len(plist)):
                file.write(f'{plist[i] - plist[i-1]}\n')
            file.close()
    dictfile.write(compression)
    for docid in docids:
        dictfile.write(' ' + docid)
    dictfile.write('\n')
    for stopword in stopwords:
        dictfile.write(stopword + ' ')
    if compression == '4':
        x = len(docids)
        bx = bin(x)[2:]
        lx = len(bx)
        blx = bin(lx)
        llx = len(blx)
        k = lx - llx
        dictfile.write(f'\n{k}')
    offset = 0
    cp = compress()
    for word in os.listdir('invidx'):
        file = open('invidx/' + word, 'r')
        plist = list(map(int, file.read().strip().split()))
        file.close()
        os.remove('invidx/' + word)
        if compression == '0':
            dictfile.write(f'\n{word} {offset} {len(plist)}')
            bytes = ''
            for index in plist:
                bytes += cp.c0(index)
            for i in range(0, len(bytes), 8):
                byte = bytes[i:min(i+8,len(bytes))]
                byte += '0'*(8-len(byte))
                idxfile.write(int.to_bytes(int(byte, 2), 1, 'big'))
                offset += 1
        if compression == '1':
            dictfile.write(f'\n{word} {offset} {len(plist)}')
            bytes = ''
            for index in plist:
                bytes += cp.c1(index)
            for i in range(0, len(bytes), 8):
                byte = bytes[i:min(i+8,len(bytes))]
                byte += '0'*(8-len(byte))
                idxfile.write(int.to_bytes(int(byte, 2), 1, 'big'))
                offset += 1
        if compression == '2':
            dictfile.write(f'\n{word} {offset} {len(plist)}')
            bytes = ''
            for index in plist:
                bytes += cp.c2(index)
            for i in range(0, len(bytes), 8):
                byte = bytes[i:min(i+8,len(bytes))]
                byte += '0'*(8-len(byte))
                idxfile.write(int.to_bytes(int(byte, 2), 1, 'big'))
                offset += 1
        if compression == '3':
            dictfile.write(f'\n{word} {offset}')
            indices = ''
            for index in plist:
                indices += str(index) + ' '
            bytes = cp.c3(indices)
            for i in range(0, len(bytes), 8):
                byte = bytes[i:min(i+8,len(bytes))]
                byte += '0'*(8-len(byte))
                idxfile.write(int.to_bytes(int(byte, 2), 1, 'big'))
                offset += 1
            dictfile.write(f' {offset}')
        if compression == '4':
            dictfile.write(f'\n{word} {offset} {len(plist)}')
            bytes = ''
            for index in plist:
                bytes += cp.c4(index, k)
            for i in range(0, len(bytes), 8):
                byte = bytes[i:min(i+8,len(bytes))]
                byte += '0'*(8-len(byte))
                idxfile.write(int.to_bytes(int(byte, 2), 1, 'big'))
                offset += 1
        if compression == '5':
            b = plist[0]
            k = len(bin(plist[(80*(len(plist)-1))//100])[2:])
            dictfile.write(f'\n{word} {offset} {len(plist)} {b} {k}')
            bytes = ''
            for index in filter(lambda x: True if x-b < 2**k-1 else False, plist):
                bytes += cp.c5(index-b, k)
            bytes += bin(2**k-1)[2:]
            for index in filter(lambda x: True if x-b > 2**k-2 else False, plist):
                bytes += cp.c1(index)
            for i in range(0, len(bytes), 8):
                byte = bytes[i:min(i+8,len(bytes))]
                byte += '0'*(8-len(byte))
                idxfile.write(int.to_bytes(int(byte, 2), 1, 'big'))
                offset += 1
    dictfile.close()
    idxfile.close()
    os.rmdir('invidx')

main()
