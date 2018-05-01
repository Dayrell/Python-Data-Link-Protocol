import sys, math, socket, time

def read_input (input_path):
    input_file = open(input_path,'rb')
    input_content = input_file.read()

    return input_content
def create_output (dados, output_path):
    file = open(output_path, 'ab')
    file.write(dados)

    file.close()

def encode16 (i, padding):
    return hex(i)[2:].zfill(padding)

def decode16 (i):
    return int(i, 16)

def string_to_hex (string, padding):
    return string.hex()

def padded_bin (i, width):
    s = bin(i)
    return s[:2] + s[2:].zfill(width)

def string_to_bin (string, padding):
    string = str(string)
    bits_string = ''

    for char in string:
        bits_string += padded_bin(ord(char), padding)[2:]
    return bits_string

def is_ack (quadro):
    tamanho = quadro[16:][:4]

    if (tamanho == '0000'):
        return True
    
    return False

def novo_quadro (quadro):
    inicio_quadro = quadro[:16]

    if (inicio_quadro == 'dcc023c2dcc023c2'):
        return True
    
    return False

## INICIO ENQUADRAMENTO ##

class Quadro:
    # constructor
    def __init__ (self):
        self.sync = 3703579586
        self.length = 0
        self.chksum = 0
        self.id = 0
        self.flags = 0

    def codifica_quadro (self, flags):
        self.sync = encode16(self.sync, 8)
        self.length = encode16(self.length, 4)
        self.chksum = encode16(self.chksum, 4)
        self.id = encode16(self.id, 2)
        self.flags = encode16(self.flags, 2)

        if(flags == 0):
            self.dados = string_to_hex(self.dados, 2)
            return (self.sync + self.sync + self.length + self.chksum + self.id + self.flags + self.dados)
        
        else:
            return (self.sync + self.sync + self.length + self.chksum + self.id + self.flags)
    
    def calcula_checksum (self, flag):
        
        sync = padded_bin(self.sync, 32)[2:]
        length = padded_bin(self.length, 16)[2:]
        chksum = padded_bin(self.chksum, 16)[2:]
        id_quadro = padded_bin(self.id, 8)[2:]
        flags = padded_bin(flag, 8)[2:]
        if(flag == 0):
            dados = string_to_bin(self.dados, 8)[2:]
            return checksum(sync + sync + length + chksum + id_quadro + flags + dados)
        else:
            return checksum(sync + sync + length + chksum + id_quadro + flags)

    def encapsula (self, indice, flags):
        if (indice % 2 == 0):
            self.id = 0
        else:
            self.id = 1

        self.flags = flags

        # self.chksum = self.calcula_checksum(flags)

        return self.codifica_quadro(flags)

    def confirmacao (self, id_quadro):
        self.flags = 128
        self.id = id_quadro

def split_len(seq, length):
    return [seq[i:i+length] for i in range(0, len(seq), length)]

def process_input (input_content):
    # definindo o tamanho maximo de caracteres de dados 
    max_length = 25000
    tamanho_entrada = len(input_content)
    num_quadros = int(math.ceil(tamanho_entrada / max_length))

    quadros = []
    conjunto_quadros = split_len(input_content, max_length)

    for i in range(0, num_quadros):
        quadro = Quadro ()
        quadro.dados = conjunto_quadros[i]
        quadro.length = len(quadro.dados)

        quadros.append(quadro)
    
    return quadros

def carry_around_add(a, b):
    c = a + b
    return(c &0xffff)+(c >>16)

def checksum (msg):
    # msg = bytearray(msg.encode('utf-8'))
    s = 0
    for i in range(0, len(msg)-1,2):
        w = (msg[i]<<8) + ((msg[i+1]))
        s = carry_around_add(s, w)
    
    return ~s &0xffff

def define_checksum (quadro):
    data = split_len (quadro,2)
    int_data = []

    for i in range(0, len(data)):
        data[i] = int(data[i], 16)

    data = quadro[:20] + hex(checksum(data))[2:].zfill(4) + quadro[24:]
    
    return data.encode('utf-8')
## TERMINO DETECCAO DE ERROS ##

## INICIO DA TRANSMISSAO/RECEPCAO ##

def inicia_comunicacao (quadros, tcp, output_path):

    quadro = quadros[0].encapsula(0, 0)
    quadro = define_checksum (quadro)
    tcp.send (quadro)
    print ('[>>]Frame length = ', len(quadros), ' bytes')

    i = 0
    dados = ''
    msg = ''
    while True:
        if (msg == ''):
            msg = (tcp.recv(1024)).decode('utf-8')
        if (novo_quadro(msg)):
            # se for novo quadro: processa
            print ('[<<]SYNC msg was found!')
            if (is_ack(msg)):
                msg = msg[28:]
                i += 1
                if (i < len(quadros)):
                    quadro = quadros[i].encapsula(i, 0)
                    quadro = define_checksum(quadro)
                    print ('[>>]Frame length = ', sys.getsizeof(quadros), ' bytes')
                    tcp.send (quadro)
                else:
                    msg = ''
            
            elif (not is_ack(msg)):
                # se nao, e um quadro com dados

                # TODO: verificar checksum
                print('[<<]Header is complete')
                print('[<<]Frame length = ', sys.getsizeof(msg), ' bytes')
                msg = msg[16:]

                length = decode16(msg[:4])
                msg = msg[4:]

                chksum = decode16(msg[:4])
                msg = msg[4:]

                print('[<<]Frame checksum = ', chksum)

                id_quadro = decode16(msg[:2])
                msg = msg[2:]

                flags = decode16(msg[:2])
                msg = msg[2:]

                # cria quadro de ack
                quadro = Quadro ()
                quadro.confirmacao(id_quadro)
                quadro = quadro.encapsula(id_quadro, 128)

                # pega dados do quadro e salva no output
                dados = ''
                dados = msg[:length * 2]
                msg = msg[length * 2:]


                while (len(dados) < length * 2):
                    print('[<<]A data frame is coming...')
                    msg = (tcp.recv(1024)).decode('utf-8')
                    
                    for char in msg:
                        if (len(dados) >= length * 2):
                            break
                        dados += char
                        msg = msg[1:]
                
                print ('[<<]Frame has been completely received')

                create_output(bytearray.fromhex(dados), output_path)
                quadro = define_checksum(quadro)
                print('[>>]ACK was sent')
                tcp.send(quadro)

## TERMINO DA TRANSMISSAO/RECEPCAO ##

## INICIO SERVER ##

def start_server (host, port, input_path, output_path):
    print('Server mode (client, use IP', socket.gethostbyname(socket.gethostname()), ')')
    
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    orig = (socket.gethostbyname(socket.gethostname()), port)
    tcp.bind(orig)
    tcp.listen(1)

    con, cliente = tcp.accept()

    input_content = read_input(input_path)

    quadros = process_input(input_content)

    inicia_comunicacao(quadros, con, output_path)

## TERMINO SERVER ##

## INICIO CLIENTE ##
def start_client (host, port, input_path, output_path):
    print('Client mode')
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dest = (host, port)

    tcp.connect(dest)

    input_content = read_input(input_path)

    quadros = process_input(input_content)

    inicia_comunicacao(quadros, tcp, output_path)

## TERMINO CLIENTE ##

if __name__ == "__main__":
    conn_type = sys.argv[1]

    if (conn_type == '-s'):
        start_server('127.0.0.1', int(sys.argv[2]), sys.argv[3], sys.argv[4])

    elif (conn_type == '-c'):
        server_address, port = sys.argv[2].split(':')
        start_client(server_address, int(port), sys.argv[3], sys.argv[4])