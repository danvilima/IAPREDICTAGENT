# Agente de Ranking e Previsão da Copa do Mundo 2026

O projeto consiste em criar um novo web app integrado ao Supabase para acompanhar os palpites da Copa do Mundo 2026 já registrados anteriormente pelos usuários.

O sistema de cadastro de palpites já existe e já está conectado ao Supabase. Portanto, este novo projeto não tem como objetivo recriar a tela de envio de palpites.

A função principal deste novo web app será acessar os palpites já salvos no banco, comparar esses palpites com os resultados reais da Copa, calcular a pontuação dos usuários em tempo real e comparar o desempenho humano com os palpites e probabilidades geradas pela IA.

A estrutura principal continua sendo a de um agente de IA que atualiza as probabilidades do torneio em tempo real, rodada a rodada. A virada de chave é que agora o sistema também terá um ranking competitivo baseado nos palpites dos usuários.

---

## Fundação do Projeto

O ponto de partida é um web app já criado anteriormente, responsável por registrar os palpites dos usuários.

Esse web app já está integrado ao Supabase e salva informações como:

* Nome do usuário.
* Campeão previsto.
* Vice-campeão previsto.
* Terceiro colocado previsto.
* Primeiro, segundo e terceiro lugar de cada grupo.
* Palpites do mata-mata.
* Palpites da final.
* Palpites da disputa de terceiro lugar.

Esses dados já estão armazenados no Supabase, principalmente na tabela de simulações ou palpites.

O novo projeto deve apenas consultar esses dados, interpretar os palpites salvos e cruzá-los com os resultados reais da Copa do Mundo 2026.

O fluxo geral será:

1. O web app antigo registra os palpites dos usuários.
2. O Supabase armazena os palpites.
3. O novo web app acessa os palpites existentes.
4. Os resultados reais da Copa são registrados ou atualizados.
5. O sistema compara palpites com resultados reais.
6. A pontuação de cada usuário é recalculada.
7. O ranking é atualizado.
8. O agente de IA interpreta o cenário e compara usuários com a IA.

---

## Objetivo Principal

O objetivo principal do projeto é transformar os palpites registrados em uma experiência interativa de acompanhamento da Copa.

O novo sistema deve responder perguntas como:

* Qual usuário está liderando o ranking?
* Quem acertou mais palpites até agora?
* Quais usuários ainda têm mais pontos possíveis?
* Quais palpites já foram perdidos?
* A IA está indo melhor ou pior que os usuários?
* Qual usuário está mais próximo dos palpites da IA?
* Qual seleção teve maior impacto nas probabilidades após a rodada?
* Quem pode assumir a liderança nas próximas fases?

O projeto une estatística, banco de dados, sistema de pontuação, ranking, simulação de Monte Carlo e agente de IA.

---

## Integração com Supabase

O Supabase será a fonte principal de dados do novo web app.

O novo app deverá se conectar ao mesmo projeto Supabase usado pelo web app antigo.

As principais tabelas envolvidas podem ser:

* `simulations`: tabela com os palpites já registrados pelos usuários.
* `real_results`: tabela com os resultados reais da Copa.
* `user_scores`: tabela com a pontuação calculada de cada usuário.
* `ai_predictions`: tabela com os palpites iniciais da IA.
* `ai_probabilities`: tabela com as probabilidades atualizadas pela IA rodada a rodada.
* `score_history`: tabela opcional para guardar histórico de pontuação após cada rodada.

A tabela `simulations` já contém os palpites dos usuários e deve ser usada como base para o sistema de ranking.

O novo app não deve apagar nem sobrescrever os palpites originais. Ele deve apenas ler esses dados e gerar cálculos derivados.

---

## Estrutura dos Palpites Existentes

Os palpites registrados no Supabase incluem previsões de fases diferentes do torneio.

Entre os campos principais estão:

* `user_name`: nome do usuário.
* `champion`: campeão previsto.
* `runner_up`: vice-campeão previsto.
* `third_place`: terceiro colocado previsto.
* `group_predictions`: previsões de primeiro e segundo lugar dos grupos.
* `third_place_predictions`: previsões de terceiros colocados dos grupos.
* Campos relacionados aos vencedores do mata-mata.

Esses dados serão comparados com o estado real da Copa.

Cada palpite poderá estar em um dos seguintes estados:

* Correto.
* Errado.
* Ainda em aberto.
* Matematicamente impossível.

Essa classificação permite mostrar não apenas a pontuação atual, mas também o potencial máximo que cada usuário ainda pode alcançar.

---

## Sistema de Pontuação

O sistema de pontuação será baseado nos acertos dos usuários em relação aos resultados reais do torneio.

A pontuação será definida da seguinte forma:

### Fase de Grupos

Cada acerto de posição nos grupos vale 1 ponto.

* Acertar o primeiro colocado de um grupo: 1 ponto.
* Acertar o segundo colocado de um grupo: 1 ponto.
* Acertar o terceiro colocado de um grupo: 1 ponto.

Exemplo:

Se o usuário acertar o primeiro, segundo e terceiro lugar do Grupo A, ele recebe 3 pontos.

### Mata-Mata

Cada acerto de vencedor em confronto de mata-mata vale 2 pontos.

Isso inclui fases como:

* 32-avos, se aplicável ao formato usado.
* Oitavas de final.
* Quartas de final.
* Semifinais.

Cada seleção corretamente prevista como vencedora de um confronto vale 2 pontos.

### Final e Disputa de Terceiro Lugar

Os acertos relacionados às decisões finais valem 3 pontos.

* Acertar o campeão: 3 pontos.
* Acertar o vice-campeão: 3 pontos.
* Acertar o terceiro colocado: 3 pontos.
* Acertar o vencedor da disputa de terceiro lugar: 3 pontos, caso esse campo seja tratado separadamente.

A pontuação deve ser transparente e exibida de forma clara no dashboard.

---

## Atualização em Tempo Real

A pontuação será sincronizada conforme as rodadas da Copa do Mundo forem acontecendo.

Sempre que um resultado real for registrado, o sistema deve:

1. Atualizar o estado real do torneio.
2. Recalcular a classificação dos grupos.
3. Verificar quais palpites foram confirmados.
4. Verificar quais palpites foram eliminados.
5. Atualizar a pontuação dos usuários.
6. Reordenar o ranking.
7. Atualizar as probabilidades da IA.
8. Comparar os usuários com a IA.
9. Exibir a nova situação no dashboard.

Assim, o ranking muda ao vivo conforme a Copa avança.

---

## Estado Real do Torneio

O novo web app precisa manter ou consultar o estado real da Copa.

Esse estado deve conter:

* Jogos realizados.
* Placar dos jogos.
* Pontuação dos grupos.
* Saldo de gols.
* Classificação atual de cada grupo.
* Seleções classificadas.
* Seleções eliminadas.
* Confrontos definidos no mata-mata.
* Vencedores de cada fase.
* Campeão, vice e terceiro colocado quando definidos.

Esse estado pode ser salvo no Supabase em uma tabela própria ou gerado a partir dos resultados reais registrados.

O estado real será a referência oficial para calcular os pontos dos usuários.

---

## Motor de Simulação

Além do ranking, o projeto mantém um motor de simulação baseado em Monte Carlo.

Esse motor roda em Python e não depende do LLM para fazer cálculos.

A lógica é:

1. Receber o estado atual real da Copa.
2. Considerar os resultados já confirmados.
3. Simular os jogos restantes milhares de vezes.
4. Usar modelo de Poisson, Elo, ranking FIFA e força estatística das seleções.
5. Calcular as probabilidades atualizadas de cada seleção.

O motor pode gerar probabilidades como:

* Chance de classificação no grupo.
* Chance de chegar às oitavas.
* Chance de chegar às quartas.
* Chance de chegar à semifinal.
* Chance de chegar à final.
* Chance de título.

Essas probabilidades serão exibidas no dashboard e usadas pelo agente de IA para gerar análises.

---

## Palpites da IA

A IA também terá seus próprios palpites.

Esses palpites podem ser gerados antes do início da Copa com base no modelo estatístico inicial.

A IA pode prever:

* Primeiro, segundo e terceiro lugar dos grupos.
* Vencedores do mata-mata.
* Campeão.
* Vice-campeão.
* Terceiro colocado.

Esses palpites devem ser salvos no Supabase para que a IA seja comparada com os usuários humanos.

É importante separar duas coisas:

1. Palpite inicial da IA.
2. Probabilidades atualizadas da IA.

O palpite inicial da IA funciona como se a IA fosse uma participante do bolão.

As probabilidades atualizadas mostram como o modelo enxerga o torneio após cada rodada.

Assim, o sistema pode comparar tanto o palpite fixo da IA quanto sua leitura estatística em tempo real.

---

## Comparação Usuários x IA

Uma das principais abas do novo web app será a comparação entre os usuários e a IA.

Essa aba deve mostrar:

* Qual usuário está liderando.
* Quantos pontos a IA teria se fosse uma participante.
* Se a IA está acima ou abaixo da média dos usuários.
* Qual usuário está mais próximo dos palpites da IA.
* Qual usuário está superando a IA.
* Qual usuário fez os palpites mais diferentes da IA.
* Quais palpites da IA já deram certo.
* Quais palpites da IA já foram eliminados.

Essa comparação transforma o projeto em uma disputa paralela:

Humanos x Inteligência Artificial.

---

## Ranking dos Usuários

O ranking dos usuários será uma das partes centrais do dashboard.

Ele deve exibir:

* Posição no ranking.
* Nome do usuário.
* Pontuação total.
* Pontos conquistados na fase de grupos.
* Pontos conquistados no mata-mata.
* Pontos conquistados na final e terceiro lugar.
* Palpites corretos.
* Palpites errados.
* Palpites ainda em aberto.
* Pontuação máxima possível restante.

Essa última informação é importante porque mostra quem ainda tem chance de virar o jogo.

Um usuário pode estar atrás no ranking atual, mas ainda ter muitos palpites futuros vivos.

---

## Agente de IA

O agente de IA será responsável por interpretar os dados e gerar respostas inteligentes.

Ele não deve calcular pontos diretamente.

Ele não deve inventar probabilidades.

Ele não deve alterar resultados reais.

O papel do agente é orquestrar tools e transformar dados em explicações claras.

O agente poderá responder perguntas como:

* Quem está liderando o bolão?
* Por que esse usuário está em primeiro?
* Quem mais ganhou pontos na última rodada?
* Quem mais perdeu chances?
* A IA está indo melhor que os usuários?
* Qual foi o palpite mais improvável que ainda está vivo?
* Quem ainda pode ultrapassar o líder?
* Qual resultado causou maior mudança nas probabilidades?

---

## Tools do Agente

O agente será estruturado com tools específicas.

As principais tools podem ser:

### Tool 1 — Consultar Palpites

Consulta no Supabase os palpites já registrados pelos usuários.

Essa tool acessa a tabela de palpites existente e retorna os dados organizados para análise.

### Tool 2 — Consultar Resultados Reais

Consulta os resultados reais da Copa já registrados no banco.

Essa tool define a realidade atual do torneio.

### Tool 3 — Calcular Score

Compara os palpites dos usuários com os resultados reais e calcula a pontuação de cada participante.

Essa tool aplica as regras:

* 1 ponto para acertos de grupo.
* 2 pontos para acertos de mata-mata.
* 3 pontos para acertos de final e terceiro lugar.

### Tool 4 — Atualizar Ranking

Ordena os usuários pela pontuação e calcula estatísticas adicionais, como pontuação máxima possível e palpites ainda vivos.

### Tool 5 — Rodar Monte Carlo

Executa o motor de simulação para atualizar as probabilidades da Copa com base no estado real atual.

### Tool 6 — Consultar Palpites da IA

Busca os palpites iniciais da IA salvos no Supabase.

### Tool 7 — Comparar Usuários x IA

Compara o score dos usuários com o score da IA.

Essa tool mostra se a IA estaria liderando, empatando ou perdendo para os participantes.

### Tool 8 — Gerar Análise Narrativa

Usa os dados calculados pelas outras tools para gerar explicações curtas e claras para o usuário.

---

## Dashboard em Streamlit

O novo web app será construído em Streamlit.

Ele terá abas principais para organizar a experiência.

### Aba 1 — Visão Geral

Mostra um resumo do torneio e do bolão.

Pode exibir:

* Líder atual.
* Pontuação do líder.
* Posição da IA.
* Quantidade de usuários participantes.
* Última rodada atualizada.
* Seleção favorita ao título segundo a IA.
* Maior subida de probabilidade.
* Maior queda de probabilidade.

### Aba 2 — Ranking dos Usuários

Mostra a tabela completa de pontuação.

Essa aba exibe quem está acertando mais de acordo com os resultados reais.

### Aba 3 — Usuários x IA

Compara os palpites dos usuários com os palpites da IA.

Mostra se a IA está melhor ou pior que os participantes humanos.

### Aba 4 — Probabilidades da IA

Mostra as probabilidades atualizadas do torneio.

Pode conter gráficos de barras, tabelas por fase e destaques das seleções favoritas.

### Aba 5 — Resultados Reais

Mostra os jogos já registrados e o estado real da Copa.

Essa aba também pode permitir o cadastro ou atualização de resultados, caso o projeto inclua essa função.

### Aba 6 — Análise do Agente

Mostra comentários gerados pelo agente sobre o cenário atual.

Exemplo:

“Daniel assumiu a liderança após acertar dois classificados do Grupo A. A IA ainda está próxima, mas perdeu força após a queda de probabilidade da França.”

---

## Modo Narrador

O Modo Narrador será usado para transformar os dados em uma explicação amigável.

Depois de cada rodada, o agente pode gerar um resumo como:

“Após os resultados da rodada, João Lucas subiu para a liderança com 12 pontos. A IA aparece em terceiro lugar, ainda competitiva, mas perdeu pontos importantes no Grupo C. O Brasil aumentou sua probabilidade de título e manteve vivos vários palpites dos usuários.”

Esse modo torna o projeto mais interessante para lives, apresentações ou acompanhamento entre amigos.

---

## Modo Palpiteiro

O Modo Palpiteiro continua existindo, mas agora com um foco mais divertido e competitivo.

Ele pode ser ativado quando:

* A IA estiver perdendo para os usuários.
* O Brasil não estiver entre os favoritos.
* Um usuário fizer uma virada grande no ranking.
* Um palpite improvável continuar vivo.
* Um favorito for eliminado.

O agente pode gerar frases curtas, provocativas e criativas.

Exemplo:

“A matemática está tentando manter a pose, mas os humanos estão dando trabalho. A IA caiu para terceiro no ranking, e o bolão virou bagunça organizada.”

Outro exemplo:

“O Brasil não lidera as probabilidades, mas torcedor brasileiro não vive de planilha. Enquanto houver jogo, há hexa.”

---

## Regras Importantes do Projeto

O novo web app não deve recriar o cadastro de palpites.

O novo web app deve acessar os palpites já salvos no Supabase.

O sistema não deve sobrescrever os palpites originais dos usuários.

A pontuação deve ser calculada a partir dos resultados reais.

O LLM não deve calcular pontos manualmente.

O LLM não deve inventar probabilidades.

O LLM não deve alterar resultados reais.

Os cálculos devem ficar em Python.

Os dados devem ficar no Supabase.

A visualização deve ficar no Streamlit.

A narrativa deve ficar com o agente.

---

## Fluxo Final Esperado

1. Usuários registram seus palpites no web app antigo.
2. Os palpites ficam salvos no Supabase.
3. O novo web app acessa a tabela de palpites existente.
4. Os resultados reais da Copa são registrados no sistema.
5. O sistema calcula os pontos de cada usuário.
6. O ranking é atualizado em tempo real.
7. O motor de Monte Carlo atualiza as probabilidades do torneio.
8. A IA compara seus palpites com os palpites dos usuários.
9. O dashboard mostra ranking, probabilidades e comparação usuários x IA.
10. O agente gera uma análise narrativa sobre o cenário atual.

---

## Objetivo Final

O objetivo final é criar um agente de IA integrado a um novo web app de acompanhamento da Copa do Mundo 2026.

Esse novo app será responsável por acessar os palpites já registrados no Supabase, calcular a pontuação dos usuários, comparar humanos contra IA e atualizar as probabilidades do torneio em tempo real.

O projeto transforma um sistema de palpites em uma experiência competitiva, estatística e interativa.

A ideia é que o usuário acompanhe não apenas quem está vencendo o bolão, mas também como a IA está se saindo contra os humanos e como cada resultado real muda completamente o cenário da Copa.

---

## Princípio Central

O cadastro de palpites já existe.

O Supabase já contém os palpites.

O novo app apenas lê, calcula, compara e visualiza.

A matemática fica no Python.

Os palpites ficam no Supabase.

O ranking fica no novo web app.

As probabilidades ficam no motor de simulação.

A explicação fica com o agente de IA.
