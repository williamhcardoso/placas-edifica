# Gerador de Placas de Obra — Edifica MT Engenharia

Aplicação de página única para gerar a arte final das placas de identificação de
obras residenciais (Minha Casa Minha Vida) e exportá-la em alta resolução para a gráfica.

**Acesso:** https://williamhcardoso.github.io/placas-edifica/

## O que faz

- Preview da placa em tempo real, na proporção física real escolhida.
- Ficha técnica com blocos opcionais (responsável, área, alvará, endereço).
- Faixa de financiamento com logos FGTS/CAIXA e logos extras.
- **Modo livre:** arrastar, redimensionar (alça ou roda do mouse) os itens da faixa
  verde e reenquadrar a fachada direto no preview.
- **Formato ajustável** (largura × altura em metros) com resolução de impressão
  selecionável — a ampliação da exportação é calculada para manter a mesma
  nitidez em qualquer tamanho de placa.
- **Biblioteca de placas** salva no navegador, com renomear, duplicar, excluir e
  exportar/importar `.json`.

## Uso

Abra a URL acima. Não há instalação nem servidor: é um único `index.html`.

Requer conexão com a internet — React, Babel, Tailwind e html-to-image vêm de CDN.

## Onde ficam as placas salvas

No `localStorage` do navegador, ou seja, **por dispositivo e por navegador**.
Para levar as placas a outro aparelho, use *Exportar .json* na seção
**Minhas placas** e *Importar .json* no destino.

A foto da fachada é comprimida (máx. 1600 px) apenas no registro salvo, para caber
no limite de ~5 MB do armazenamento local — a imagem exibida e exportada durante a
sessão continua sendo a original.

## Desenvolvimento

Todo o app está em `index.html`: React 18 (UMD) + Babel standalone + Tailwind (CDN)
e `html-to-image` para a exportação PNG. As logos e a fachada padrão estão embutidas
em base64. Basta editar o arquivo e abrir no navegador.
