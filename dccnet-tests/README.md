# DCCNET testing infrastructure

Este pacote apresenta uma implementação do DCCNET e casos de teste
que você pode utilizar durante a avaliação do DCCNET.  O seu
programa deverá interoperar com outros, incluindo o fornecido neste
pacote (compilado para Linux/amd64).  Por isso, é recomendado que
você o utilize em alguma etapa dos seus testes.

O programa fornecido apresenta algumas mensagens na saída padrão.
Elas podem ser úteis durante os testes.  Execute algum exemplo onde
tanto o servidor quanto o cliente são o `dcc023c2` fornecido. Assim,
você se familiariza com as mensagens.

## Casos de teste

O diretório `tests` tem cinco casos de testes que você pode utilizar
para testar seu programa.  Os arquivos sem sufixo são os arquivos
originais, que podem ser utilizados como entrada do programa.  Ou
seja, dados a serem transmitidos por um programa e,
consequentemente, recebidos pela outro programa.

Os arquivos com sufixo `-hex` apresentam os dados do arquivo
*enquadrados e codificados*, sem erro e prontos para transmissão via
rede.

Arquivos com dados binários não codificados, dispostos um byte por
linha. Trata-se da entrada do codificador ou da saída do
decodificador.

Para fins de teste e desambiguamento, o arquivo `hello-bin.txt`
mostra os bits (8 bits por linha) de um quadro transmitindo
o conteúdo do arquivo `hello.txt`.

## Testes usando o socat

Os arquivos com sufixo `-hex` podem ser utilizados para testes
isolados.  Para isso, você pode utilizar a ferramenta `socat`
(https://linux.die.net/man/1/socat).  Essa ferramenta envia fluxos
de bytes através de soquetes.  Portanto, `socat` pode ser utilizada
para enviar dados para um programa implementando o DCCNET, que deve
receber os dados normalmente.  Por exemplo, você pode executar um
servidor DCCNET:

```{bash}
$ echo "executando um servidor DCCNET"
$ ./dcc023c2 -s 5151 tests/hello.txt hello-recebido.txt
```

E depois executar simular um cliente usando o `socat`.  Neste
exemplo, o socat transmitiria um quadro codificado contendo
o conteúdo do arquivo `tests/hello.txt`:

```{bash}
$ echo "simulando um cliente"
$ socat TCP:127.0.0.1:5151 "tests/hello-hex.txt"
```

Uma vez que o arquivo `tests/hello-hex.txt` consiste nos bytes
enviados pelo lado cliente para transmissão do arquivo
`tests/hello.txt`, o arquivo `hello-recebido.txt` deverá ser
idêntico ao arquivo `tests/hello.txt`.

Lembre-se que o arquivo de saída do receptor deve ser exatamente
igual ao arquivo de entrada do transmissor. Para verificar que os
arquivos são idênticos, use ferramentas de comparação de arquivos
como a `diff` ou de sumarização como `sha256sum`.  Exemplo: `diff
tests/hello.txt hello-recebido.txt` para o caso do exemplo anterior.

