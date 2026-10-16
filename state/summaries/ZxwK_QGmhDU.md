## NOVAS MUDANÇAS NA NFS-E PARA A REFORMA TRIBUTÁRIA

**Em uma frase:** A nova versão da Nota Técnica 009 da NFS-e, publicada em outubro, traz novos campos e grupos para adaptar a nota fiscal de serviço ao IBS e à CBS, incluindo regras para condomínios e comércio exterior, mas ainda não tem data de início.

### Principais pontos

1. **Nova versão da NT 009:** Uma versão prévia da Nota Técnica 009 tinha saído em junho, sem cronograma de implantação. A versão de outubro corrige pontos das anteriores e cria novos campos e grupos. A NFS-e está sendo reformulada para cobrir tanto as operações já tributadas pelo ISS quanto as que não tinham incidência do imposto.

2. **Ainda não está em produção:** As mudanças da NT 009 terão data de implementação futura. O cronograma será divulgado no Portal Nacional da NFS-e e ainda não foi publicado.

3. **O que a NT 009 já previa:**
   - notas de ajuste de débito e crédito para IBS e CBS;
   - evoluções para empresas do Simples Nacional, com campos para identificar a receita bruta e informar IBS e CBS para quem optar por recolher esses tributos dentro do regime;
   - reestruturação das informações sobre bens imóveis;
   - criação do grupo de vínculo de pagamento, que a NFS-e ainda não tinha e que será necessário por causa do *split payment*.

4. **Novidades desta versão:**
   - **Versão da calculadora de IBS/CBS:** um novo grupo informa qual versão da calculadora foi usada. Quem preenche é o próprio portal, não o contribuinte.
   - **Validação de endereço:** novas regras de validação para o endereço do tomador e do destinatário, usadas para definir o local de incidência do ISS no código de tributação nacional 1705.
   - **Indicação do destinatário:** essa informação passou para dentro do grupo da DPS e saiu da NFS-e.
   - **Comércio exterior:** foram incluídos e atualizados campos nesse grupo. Um deles é o novo campo de ajuste da base de cálculo de IBS/CBS, usado quando a operação é em moeda estrangeira e há variação cambial. Esse ajuste funciona de forma diferente do ISS e dos tributos federais.
   - **Eventos:** novo campo para o município onde o evento acontece, que pode ser diferente do município do tomador.

5. **Operações de condomínio:** O Ato Conjunto nº 4 já previa que condomínios começariam a informar IBS e CBS na NFS-e a partir de dezembro, mas até agora não havia campos para isso. A nova versão cria:
   - o código **990501 (operações condominiais)**, na lista de operações sem incidência de ISS;
   - um grupo específico com dados da cobrança e o detalhamento do que está sendo cobrado (por exemplo, telefone, internet e gás), além de eventual desconto incondicionado.

   O vídeo ressalta que ainda não está expresso se todo condomínio será obrigado a emitir NFS-e. O grupo serve para entender como funcionará para quem precisar emitir.

6. **CST e cClassTrib reposicionados:** Esses campos saíram de dentro do grupo de IBS/CBS e agora vêm antes dele. Dependendo do código escolhido, o grupo de IBS/CBS nem precisa ser preenchido, como já acontece nos outros documentos fiscais eletrônicos. Exemplo: com o CST 400 (isenção/imunidade), a operação não tem tributação e o grupo é dispensado. Os campos relacionados foram ajustados por causa dessa mudança no layout.

### Detalhes que valem atenção

- **Nota Técnica 009 da NFS-e:** versão prévia em junho e nova versão em outubro, ainda sem data de início. O cronograma sairá no Portal Nacional.
- **Ato Conjunto nº 4:** define o início da obrigatoriedade de informar IBS e CBS nos documentos fiscais, com início previsto para dezembro no caso de condomínios na NFS-e.
- **Código 990501:** operações condominiais, entre os códigos sem incidência de ISS.
- **Código de tributação nacional 1705:** recebeu novas regras de validação de endereço para definir o local de incidência do ISS.
- **CST 400 (isenção/imunidade):** dispensa o preenchimento do grupo de IBS/CBS.
- **Split payment:** é o motivo da criação do grupo de vínculo de pagamento na NFS-e.
- **Recomendação:** acompanhar as publicações no Portal Nacional da NFS-e para saber quando as mudanças entram em vigor.

### Para quem é útil

Contadores, desenvolvedores de software fiscal e empresas prestadoras de serviço, principalmente quem lida com locação, condomínios, eventos, comércio exterior ou Simples Nacional e precisa se preparar para o IBS e a CBS na NFS-e.
