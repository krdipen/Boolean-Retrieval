import re, sys, snappy
sys.path.append('.')
from stemmer import PorterStemmer

class decompress:

    def c0(self, idxfile, data):
        plist = []
        idxfile.seek(data[0])
        for i in range(0, data[1]):
            index = ''
            while True:
                byte = bin(int.from_bytes(idxfile.read(1), 'big'))[2:]
                byte = '0' * (8-len(byte)) + byte
                ch = chr(int(byte, 2))
                if ch == ' ':
                    break
                index += ch
            plist.append(int(index))
        return plist
        
    def c1(self, idxfile, data):
        plist = []
        idxfile.seek(data[0])
        for i in range(0, data[1]):
            index = ''
            while True:
                byte = bin(int.from_bytes(idxfile.read(1), 'big'))[2:]
                byte = '0' * (8-len(byte)) + byte
                index += byte[1:]
                if byte[0] == '0':
                    break
            plist.append(int(index,2))
        return plist

    def c2(self, idxfile, data):
        plist = []
        idxfile.seek(data[0])
        state, x, bx, lx, blx, llx, count  = 0, 1, '1', 1, '1', 0, data[1]
        while count > 0:
            byte = bin(int.from_bytes(idxfile.read(1), 'big'))[2:]
            byte = '0' * (8-len(byte)) + byte
            for i in range(0, 8):
                if state == 0:
                    llx += 1
                    if byte[i] == '0':
                        if llx > 1:
                            state = 1
                            continue
                        else:
                            state = 3
                if state == 1:
                    llx -= 1
                    blx += byte[i]
                    if llx == 1:
                        state = 2
                        lx = int(blx, 2)
                        continue
                if state == 2:
                    lx -= 1
                    bx += byte[i]
                    if lx == 1:
                        state = 3
                        x = int(bx, 2)
                if state == 3:
                    plist.append(x)
                    state, x, bx, lx, blx, llx  = 0, 1, '1', 1, '1', 0
                    count -= 1
                    if count == 0:
                        break
        return plist

    def c3(self, idxfile, data):
        plist = []
        idxfile.seek(data[0])
        bytes = idxfile.read(data[1] - data[0])
        indices = snappy.decompress(bytes).decode()
        plist = list(map(int, indices.strip().split()))
        return plist

    def c4(self, idxfile, data, k):
        plist = []
        idxfile.seek(data[0])
        state, q, r, x, l, count = 0, 0, '', 0, 0, data[1]
        while count > 0:
            byte = bin(int.from_bytes(idxfile.read(1), 'big'))[2:]
            byte = '0' * (8-len(byte)) + byte
            for i in range(0, 8):
                if state == 0:
                    q += 1
                    if byte[i] == '0':
                        state = 1
                        continue
                if state == 1:
                    l += 1
                    r += byte[i]
                    if l == k:
                        state = 2
                        x = ((q-1) * (2**k)) + int(r, 2) + 1
                if state == 2:
                    plist.append(x)
                    state, q, r, x, l  = 0, 0, '', 0, 0
                    count -= 1
                    if count == 0:
                        break
        return plist

    def c5(self, idxfile, data):
        plist = []
        idxfile.seek(data[0])
        state, prev, r, l, x = 0, 0, '', 0, ''
        k = data[3]
        b = data[2]
        count = data[1]
        while count > 0:
            byte = bin(int.from_bytes(idxfile.read(1), 'big'))[2:]
            byte = '0' * (8-len(byte)) + byte
            for i in range(0, 8):
                if state == 0:
                    l += 1
                    x += byte[i]
                    if l == k:
                        x = int(x, 2)
                        if x == 2**k - 1:
                            state, r, l, x = 1, '', 0, ''
                            continue
                        else:
                            state, prev, x = 2, 0, x + b
                if state == 1:
                    l += 1
                    r += byte[i]
                    if l == 8:
                        x = x + r[1:]
                        if r[0] == '0':
                            state, prev, x = 2, 1, int(x, 2)
                        r, l = '', 0
                if state == 2:
                    plist.append(x)
                    state, r, l, x = prev, '', 0, '',
                    count -= 1
                    if count == 0:
                        break
        return plist

def main():

    dictfile = open(sys.argv[4], 'r')
    docids = dictfile.readline().strip().split()
    stopwords = list(map(str.lower, dictfile.readline().strip().split()))
    compression = docids[0]
    if compression == '4':
        k = int(dictfile.readline().strip())
    data = {}
    for line in dictfile:
        pair = line.strip().split()
        data[pair[0]] = list(map(int, pair[1:]))
    dictfile.close()
    
    count = 0
    ps = PorterStemmer()
    dcp = decompress()
    queryfile = open(sys.argv[1], 'r')
    resultfile = open(sys.argv[2], 'w')
    idxfile = open(sys.argv[3], 'rb')
    for line in queryfile:
        tokens = re.split('[.,:;\\\\/\n\t\s\r\'\"\(\)\[\]\{\}]', line.strip())
        tokens = filter(lambda x : True if len(x) > 0 else False, tokens)
        terms = [ps.stem(token, 0, len(token)-1).lower() for token in tokens]
        terms = [term for term in terms if term not in stopwords]
        empty = True
        results = set()
        for term in terms:
            if term not in data:
                plist = []
            elif compression == '0':
                plist = dcp.c0(idxfile, data[term])
            elif compression == '1':
                plist = dcp.c1(idxfile, data[term])
            elif compression == '2':
                plist = dcp.c2(idxfile, data[term])
            elif compression == '3':
                plist = dcp.c3(idxfile, data[term])
            elif compression == '4':
                plist = dcp.c4(idxfile, data[term], k)
            elif compression == '5':
                plist = dcp.c5(idxfile, data[term])
            if compression in ['1', '2', '3', '4']:
                for i in range(1, len(plist)):
                    plist[i] = plist[i-1] + plist[i]
            if empty:
                empty = False
                results = set(plist)
            else:
                results = results.intersection(plist)
        for result in results:
            resultfile.write(f'Q{count} {docids[result]} 1.0\n')
        count += 1
    idxfile.close()
    resultfile.close()
    queryfile.close()

main()
