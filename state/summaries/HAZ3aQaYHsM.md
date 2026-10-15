## COMO DEFINIR O CST NAS NOTAS FISCAIS CORRETAMENTE

**Em uma frase:** Para definir o CST e o cClassTrib do IBS/CBS numa nota fiscal, é preciso analisar a natureza da operação (onerosa ou não, com imunidade ou não incidência) e também o produto ou serviço (NCM/NBS **e** descrição), seguindo um fluxo de perguntas.

### Principais pontos

1. **Conhecer a tributação de cada item antes de configurar o sistema.** Ao parametrizar o sistema emissor, o escritório precisa saber se cada produto ou serviço da empresa tem alguma tributação diferenciada. A classificação fica vinculada à NCM (produtos) ou à NBS (serviços).

2. **Olhar também para a operação, não só para o item.** O mesmo produto pode ter tratamentos diferentes conforme a operação: venda, transferência, remessa etc. A apresentadora sugere um fluxograma de perguntas para chegar ao código correto. Ela ressalta que o fluxograma não resolve tudo, mas dá um bom norte.

3. **A regra geral é tributar o fornecimento oneroso.** Com a reforma tributária, o IBS/CBS incide, em regra, quando há contraprestação, ou seja, quando a empresa cobra pela mercadoria ou pelo serviço. Existem exceções nos dois sentidos: operações onerosas que não são tributadas e operações não onerosas que são.

4. **Caminho do fornecimento oneroso:**
   - **Primeira pergunta:** a operação se enquadra em alguma hipótese de imunidade ou não incidência prevista na legislação do IBS/CBS? Se sim, usa-se o **CST 410** e escolhe-se o cClassTrib específico. Exemplo: a exportação é onerosa, mas imune, e usa o código 410.004 (exportação de bens e serviços). Nesse caso, a operação define a classificação independentemente da tributação do produto.
   - **Segunda pergunta:** se não há imunidade, o produto ou serviço tem algum benefício? Se não tiver, aplica-se a tributação geral, com **CST 000**. Se tiver, usam-se o CST e o cClassTrib próprios do benefício.

5. **Caminho do fornecimento não oneroso:**
   - Em regra, não há tributação. Mas o regulamento prevê exceções em que o IBS/CBS é exigido mesmo sem cobrança.
   - **Exemplo de exceção, a bonificação:** se não estiver vinculada à nota fiscal de venda e depender de um evento posterior, ela é tributada. Nesse caso, segue-se o mesmo fluxo do fornecimento oneroso, verificando se o produto tem benefício.
   - **Se não estiver nas exceções:** usa-se o CST 410 com o cClassTrib específico. Se não houver código específico, usa-se o genérico **410.999**. O exemplo dado é a remessa para conserto.
   - O código genérico só vale quando não existe um específico. Se houver código específico, ele é obrigatório.

6. **Como pesquisar benefícios.** Há três caminhos: consultar a Lei Complementar 214 (por NCM ou descrição), percorrer a tabela de cClassTrib (que indica a base legal de cada código para conferência) ou usar o assistente de classificação do portal Conformidade Fácil.

7. **A NCM sozinha não basta.** O exemplo do pão ilustra isso. O pão francês da cesta básica tem redução de 100% e usa **CST 200** com **cClassTrib 200.003**. Já o pão de queijo, com a mesma NCM, não atende à descrição do benefício e é tributado normalmente. É sempre necessário confrontar a descrição do produto ou serviço com o texto do benefício.

### Detalhes que valem atenção

- **Códigos citados:**
  - CST 410: imunidade e não incidência.
    - 410.004: exportação de bens e serviços.
    - 410.999: código genérico para operações não tributadas sem código específico.
  - CST 000: tributação integral, sem benefício.
  - CST 200 / cClassTrib 200.003: redução de 100%, exemplo do pão francês da cesta básica.
- **Norma:** Lei Complementar 214 e o regulamento do IBS/CBS, com os artigos sobre imunidade, não incidência e exceções para fornecimentos não onerosos.
- **Ferramentas:**
  - Portal dos Documentos Fiscais Eletrônicos, área **Conformidade Fácil** > Serviços > **Tabela de Classificação Tributária**. Ao clicar em cada CST, a tabela mostra os cClassTrib correspondentes. A apresentadora observa que a tabela tem sido atualizada, então convém consultar a versão mais recente.
  - **Assistente para Classificação Tributária**, no mesmo portal. É gratuito e busca NCMs compatíveis com uma descrição, indicando possíveis benefícios. Deve ser usado como apoio, não como resposta definitiva.
  - A tabela de cClassTrib também está disponível no portal da NF-e.
  - Existem ferramentas pagas que fazem essa classificação.
- **Bonificação:** só é tributada quando não está vinculada à nota de venda e depende de evento posterior.
- **Escopo:** o fluxo trata apenas de IBS/CBS. ICMS, PIS/COFINS, IPI e os demais códigos da nota continuam precisando ser definidos à parte.

### Para quem é útil

Contadores e analistas fiscais que parametrizam sistemas emissores de nota fiscal para a reforma tributária, e donos de escritório que precisam orientar clientes sobre a classificação de IBS/CBS por operação e por produto.
