#############################################################
## SCRIPT 01
## IMPORTAÇÃO, LIMPEZA E ANÁLISE EXPLORATÓRIA
## Projeto: Startup Profit Prediction
#############################################################

rm(list=ls())

graphics.off()

cat("\014")

set.seed(1234)

#############################################################
## PACOTES
#############################################################

packages <- c(
  
  "tidyverse",
  
  "psych",
  
  "skimr",
  
  "GGally",
  
  "corrplot",
  
  "ggpubr",
  
  "reshape2",
  
  "gridExtra",
  
  "openxlsx"
  
)

instalar <- packages[!(packages %in% installed.packages()[,1])]

if(length(instalar)>0){
  
  install.packages(instalar)
  
}

invisible(lapply(packages,
                 library,
                 character.only=TRUE))

theme_set(theme_bw(base_size=14))

#############################################################
## CRIA PASTAS
#############################################################

dir.create("Resultados",showWarnings = FALSE)

dir.create("Resultados/Figuras",showWarnings = FALSE)

dir.create("Resultados/Tabelas",showWarnings = FALSE)

#############################################################
## IMPORTAÇÃO
#############################################################

dados <- read.csv(text="
R.D.Spend,Administration,Marketing.Spend,State,Profit
165349.2,136897.8,471784.1,New York,192261.83
162597.7,151377.59,443898.53,California,191792.06
153441.51,101145.55,407934.54,Florida,191050.39
144372.41,118671.85,383199.62,New York,182901.99
142107.34,91391.77,366168.42,Florida,166187.94
131876.9,99814.71,362861.36,New York,156991.12
134615.46,147198.87,127716.82,California,156122.51
130298.13,145530.06,323876.68,Florida,155752.6
120542.52,148718.95,311613.29,New York,152211.77
123334.88,108679.17,304981.62,California,149759.96
101913.08,110594.11,229160.95,Florida,146121.95
100671.96,91790.61,249744.55,California,144259.4
93863.75,127320.38,249839.44,Florida,141585.52
91992.39,135495.07,252664.93,California,134307.35
119943.24,156547.42,256512.92,Florida,132602.65
114523.61,122616.84,261776.23,New York,129917.04
78013.11,121597.55,264346.06,California,126992.93
94657.16,145077.58,282574.31,New York,125370.37
91749.16,114175.79,294919.57,Florida,124266.9
86419.7,153514.11,0,New York,122776.86
76253.86,113867.3,298664.47,California,118474.03
78389.47,153773.43,299737.29,New York,111313.02
73994.56,122782.75,303319.26,Florida,110352.25
67532.53,105751.03,304768.73,Florida,108733.99
77044.01,99281.34,140574.81,New York,108552.04
64664.71,139553.16,137962.62,California,107404.34
75328.87,144135.98,134050.07,Florida,105733.54
72107.6,127864.55,353183.81,New York,105008.31
66051.52,182645.56,118148.2,Florida,103282.38
65605.48,153032.06,107138.38,New York,101004.64
61994.48,115641.28,91131.24,Florida,99937.59
61136.38,152701.92,88218.23,New York,97483.56
63408.86,129219.61,46085.25,California,97427.84
55493.95,103057.49,214634.81,Florida,96778.92
46426.07,157693.92,210797.67,California,96712.8
46014.02,85047.44,205517.64,New York,96479.51
28663.76,127056.21,201126.82,Florida,90708.19
44069.95,51283.14,197029.42,California,89949.14
20229.59,65947.93,185265.1,New York,81229.06
38558.51,82982.09,174999.3,California,81005.76
28754.33,118546.05,172795.67,California,78239.91
27892.92,84710.77,164470.71,Florida,77798.83
23640.93,96189.63,148001.11,California,71498.49
15505.73,127382.3,35534.17,New York,69758.98
22177.74,154806.14,28334.72,California,65200.33
1000.23,124153.04,1903.93,New York,64926.08
1315.46,115816.21,297114.46,Florida,49490.75
0,135426.92,0,California,42559.73
542.05,51743.15,0,New York,35673.41
0,116983.8,45173.06,California,14681.4")

#############################################################
## ORGANIZAÇÃO
#############################################################

dados$State <- factor(dados$State)

str(dados)

glimpse(dados)

head(dados)

tail(dados)

dim(dados)

#############################################################
## VALORES AUSENTES
#############################################################

colSums(is.na(dados))

#############################################################
## ESTATÍSTICA DESCRITIVA
#############################################################

desc <- psych::describe(dados)

desc

write.xlsx(desc,
           "Resultados/Tabelas/Estatistica_Descritiva.xlsx",
           overwrite=TRUE)

#############################################################
## RESUMO GERAL
#############################################################

skim(dados)

#############################################################
## HISTOGRAMAS
#############################################################

#############################################################
## HISTOGRAMAS DAS VARIÁVEIS NUMÉRICAS
#############################################################

dados_hist <- dados |>
  pivot_longer(
    cols = where(is.numeric),
    names_to = "Variavel",
    values_to = "Valor"
  )

g_hist <- ggplot(
  dados_hist,
  aes(x = Valor)
) +
  geom_histogram(
    bins = 20,
    fill = "steelblue",
    color = "black",
    alpha = 0.8
  ) +
  facet_wrap(
    ~Variavel,
    scales = "free"
  ) +
  theme_bw(base_size = 14)

ggsave(
  "Resultados/Figuras/Histogramas.png",
  g_hist,
  width = 10,
  height = 8,
  dpi = 600
)

#############################################################
## BOXPLOTS
#############################################################

#############################################################
## BOXPLOTS DAS VARIÁVEIS NUMÉRICAS
#############################################################

library(ggplot2)
library(tidyr)

dados_long <- dados |>
  pivot_longer(
    cols = c(R.D.Spend,
             Administration,
             Marketing.Spend,
             Profit),
    names_to = "Variavel",
    values_to = "Valor"
  )

ggplot(dados_long,
       aes(x = Variavel,
           y = Valor,
           fill = Variavel)) +
  geom_boxplot(alpha = 0.8) +
  theme_bw(base_size = 14) +
  theme(legend.position = "none")

#############################################################
## MATRIZ DE DISPERSÃO
#############################################################

GGally::ggpairs(
  
  dados,
  
  columns=c(1,2,3,5),
  
  aes(color=State)
  
)

#############################################################
## MATRIZ DE CORRELAÇÃO
#############################################################

correlacao <- cor(
  
  dados %>%
    
    select(R.D.Spend,
           Administration,
           Marketing.Spend,
           Profit)
  
)

round(correlacao,3)

corrplot(
  
  correlacao,
  
  method="color",
  
  type="upper",
  
  addCoef.col="black",
  
  number.cex=.8,
  
  tl.cex=.9
  
)

#############################################################
## BOXPLOTS POR ESTADO
#############################################################

ggplot(
  
  dados,
  
  aes(State,
      Profit,
      fill=State)
  
)+
  
  geom_boxplot(
    
    alpha=.8
    
  )+
  
  theme_bw()

#############################################################
## DENSIDADE
#############################################################

ggplot(
  
  dados,
  
  aes(Profit)
  
)+
  
  geom_density(
    
    fill="steelblue",
    
    alpha=.4
    
  )

#############################################################
## EXPORTAÇÃO
#############################################################

write.csv(
  
  dados,
  
  "Resultados/Tabelas/Base_Organizada.csv",
  
  row.names=FALSE
  
)

save(
  
  dados,
  
  file="Resultados/Base.RData"
  
)

cat("SCRIPT 01 FINALIZADO\n")

#############################################################
## SCRIPT 02
## REGRESSÃO LINEAR MÚLTIPLA
## DIAGNÓSTICO DOS PRESSUPOSTOS
#############################################################

cat("\014")

#############################################################
## PACOTES
#############################################################

packages <- c(
  
  "car",
  "lmtest",
  "performance",
  "olsrr",
  "broom",
  "see"
  
)

instalar <- packages[!(packages %in% installed.packages()[,1])]

if(length(instalar)>0){
  
  install.packages(instalar)
  
}

invisible(lapply(packages,
                 library,
                 character.only=TRUE))

#############################################################
## MODELO LINEAR COMPLETO
#############################################################

modelo <- lm(
  
  Profit ~
    R.D.Spend +
    Administration +
    Marketing.Spend +
    State,
  
  data=dados
  
)

summary(modelo)

#############################################################
## COEFICIENTES
#############################################################

coeficientes <- broom::tidy(
  
  modelo,
  conf.int=TRUE
  
)

coeficientes

write.xlsx(
  
  coeficientes,
  
  "Resultados/Tabelas/Coeficientes_Modelo.xlsx",
  
  overwrite=TRUE
  
)

#############################################################
## ANOVA DO MODELO
#############################################################

anova(modelo)

#############################################################
## QUALIDADE DO AJUSTE
#############################################################

glance(modelo)

#############################################################
## MULTICOLINEARIDADE
#############################################################

vif_modelo <- car::vif(modelo)

vif_modelo

write.xlsx(
  
  as.data.frame(vif_modelo),
  
  "Resultados/Tabelas/VIF.xlsx",
  
  overwrite=TRUE
  
)

#############################################################
## NORMALIDADE DOS RESÍDUOS
#############################################################

shapiro.test(
  
  residuals(modelo)
  
)

#############################################################
## HOMOCEDASTICIDADE
#############################################################

bptest(modelo)

#############################################################
## AUTOCORRELAÇÃO
#############################################################

dwtest(modelo)

#############################################################
## INFLUÊNCIA DAS OBSERVAÇÕES
#############################################################

cook <- cooks.distance(modelo)

hat <- hatvalues(modelo)

rstudent <- rstudent(modelo)

dffits_val <- dffits(modelo)

dfbetas_val <- dfbetas(modelo)

#############################################################
## TABELA DE DIAGNÓSTICO
#############################################################

diagnostico <- data.frame(
  
  Observacao=1:nrow(dados),
  
  Cook=cook,
  
  Leverage=hat,
  
  RStudent=rstudent,
  
  DFFITS=dffits_val
  
)

diagnostico

write.xlsx(
  
  diagnostico,
  
  "Resultados/Tabelas/Diagnostico_Observacoes.xlsx",
  
  overwrite=TRUE
  
)

#############################################################
## LIMITES
#############################################################

n <- nrow(dados)

p <- length(coef(modelo))

cook_limite <- 4/n

lev_limite <- 2*p/n

dffits_limite <- 2*sqrt(p/n)

cat("\n")

cat("Cook limite =",cook_limite,"\n")

cat("Leverage limite =",lev_limite,"\n")

cat("DFFITS limite =",dffits_limite,"\n")

#############################################################
## OBSERVAÇÕES POTENCIALMENTE INFLUENTES
#############################################################

infl <- diagnostico |>
  
  dplyr::filter(
    
    Cook>cook_limite |
      
      Leverage>lev_limite |
      
      abs(RStudent)>3 |
      
      abs(DFFITS)>dffits_limite
    
  )

infl

write.xlsx(
  
  infl,
  
  "Resultados/Tabelas/Observacoes_Influentes.xlsx",
  
  overwrite=TRUE
  
)

#############################################################
## DFBETAS
#############################################################

dfbetas_df <- as.data.frame(dfbetas_val)

write.xlsx(
  
  dfbetas_df,
  
  "Resultados/Tabelas/DFBETAS.xlsx",
  
  overwrite=TRUE
  
)

#############################################################
## GRÁFICOS CLÁSSICOS
#############################################################

png(
  
  "Resultados/Figuras/Diagnosticos_Classicos.png",
  
  width=2400,
  
  height=1800,
  
  res=300
  
)

par(
  
  mfrow=c(2,2)
  
)

plot(modelo)

dev.off()

#############################################################
## COOK DISTANCE
#############################################################

png(
  
  "Resultados/Figuras/CookDistance.png",
  
  width=2200,
  
  height=1400,
  
  res=300
  
)

plot(
  
  cook,
  
  type="h",
  
  ylab="Cook Distance",
  
  xlab="Observação"
  
)

abline(
  
  h=cook_limite,
  
  col=2,
  
  lwd=2,
  
  lty=2
  
)

dev.off()

#############################################################
## LEVERAGE
#############################################################

png(
  
  "Resultados/Figuras/Leverage.png",
  
  width=2200,
  
  height=1400,
  
  res=300
  
)

plot(
  
  hat,
  
  type="h",
  
  ylab="Leverage"
  
)

abline(
  
  h=lev_limite,
  
  col=2,
  
  lwd=2,
  
  lty=2
  
)

dev.off()

#############################################################
## RESÍDUOS STUDENTIZADOS
#############################################################

png(
  
  "Resultados/Figuras/Residuos_Studentizados.png",
  
  width=2200,
  
  height=1400,
  
  res=300
  
)

plot(
  
  rstudent,
  
  type="h",
  
  ylab="Studentized Residual"
  
)

abline(
  
  h=c(-3,3),
  
  col=2,
  
  lwd=2,
  
  lty=2
  
)

dev.off()

#############################################################
## QQPLOT
#############################################################

png(
  
  "Resultados/Figuras/QQPlot.png",
  
  width=2200,
  
  height=2200,
  
  res=300
  
)

qqPlot(
  
  modelo,
  
  id=FALSE
  
)

dev.off()

#############################################################
## OBSERVADO VS AJUSTADO
#############################################################

pred <- fitted(modelo)

graf <- data.frame(
  
  Observado=dados$Profit,
  
  Predito=pred
  
)

g1 <- ggplot(
  
  graf,
  
  aes(
    
    Observado,
    
    Predito
    
  )
  
)+
  
  geom_point(
    
    size=3,
    
    colour="steelblue"
    
  )+
  
  geom_abline(
    
    slope=1,
    
    intercept=0,
    
    colour="red",
    
    linewidth=1
    
  )+
  
  theme_bw()

ggsave(
  
  "Resultados/Figuras/Observado_vs_Predito_LM.png",
  
  g1,
  
  width=6,
  
  height=6,
  
  dpi=600
  
)

#############################################################
## RESÍDUOS
#############################################################

g2 <- ggplot(
  
  data.frame(
    
    Predito=pred,
    
    Residuo=residuals(modelo)
    
  ),
  
  aes(
    
    Predito,
    
    Residuo
    
  )
  
)+
  
  geom_point(
    
    size=3,
    
    colour="darkgreen"
    
  )+
  
  geom_hline(
    
    yintercept=0,
    
    linetype=2,
    
    colour="red"
    
  )+
  
  theme_bw()

ggsave(
  
  "Resultados/Figuras/Residuos_vs_Preditos.png",
  
  g2,
  
  width=6,
  
  height=6,
  
  dpi=600
  
)

#############################################################
## SELEÇÃO DAS OBSERVAÇÕES
#############################################################

cat("\n")

cat("----------------------------------------\n")

cat("Número de observações influentes:\n")

nrow(infl)

cat("----------------------------------------\n")

#############################################################
## BASE PARA ML
#############################################################

## A decisão será tomada pelo pesquisador.
## Se desejar remover observações influentes:

dados_ml <- dados

## Caso decida remover posteriormente:
##
## dados_ml <- dados[-infl$Observacao, ]

save(
  
  dados_ml,
  
  file="Resultados/dados_ml.RData"
  
)

cat("\n")

cat("SCRIPT 02 FINALIZADO\n")

#############################################################
## SCRIPT 03
## PREPARAÇÃO PARA MACHINE LEARNING
#############################################################

cat("\014")

#############################################################
## PACOTES
#############################################################

packages <- c(
  
  "caret",
  "recipes",
  "doParallel",
  "dplyr",
  "fastDummies"
  
)

instalar <- packages[!(packages %in% installed.packages()[,1])]

if(length(instalar)>0){
  
  install.packages(instalar)
  
}

invisible(lapply(packages,
                 library,
                 character.only=TRUE))

#############################################################
## SEMENTE
#############################################################

set.seed(2026)

#############################################################
## BASE UTILIZADA
#############################################################

dados_modelo <- dados_ml

#############################################################
## CONFERÊNCIA
#############################################################

str(dados_modelo)

summary(dados_modelo)

#############################################################
## TRANSFORMA STATE EM FATOR
#############################################################

dados_modelo$State <-
  
  factor(
    
    dados_modelo$State
    
  )

#############################################################
## DIVISÃO TREINO/TESTE
#############################################################

train_index <-
  
  createDataPartition(
    
    dados_modelo$Profit,
    
    p=.80,
    
    list=FALSE
    
  )

train <- dados_modelo[train_index,]

test <- dados_modelo[-train_index,]

#############################################################
## TAMANHO DAS AMOSTRAS
#############################################################

cat("\n")

cat("Treino :",nrow(train),"\n")

cat("Teste  :",nrow(test),"\n")

#############################################################
## EXPORTAÇÃO
#############################################################

write.csv(
  
  train,
  
  "Resultados/Tabelas/Base_Treinamento.csv",
  
  row.names=FALSE
  
)

write.csv(
  
  test,
  
  "Resultados/Tabelas/Base_Teste.csv",
  
  row.names=FALSE
  
)

#############################################################
## DUMMY VARIABLES
#############################################################

dummy <- dummyVars(
  
  Profit~.,
  
  data=train,
  
  fullRank=TRUE
  
)

#############################################################
## MATRIZES NUMÉRICAS
#############################################################

x_train <-
  
  predict(
    
    dummy,
    
    train
    
  )

x_test <-
  
  predict(
    
    dummy,
    
    test
    
  )

x_train <- as.data.frame(x_train)

x_test <- as.data.frame(x_test)

#############################################################
## VARIÁVEIS RESPOSTA
#############################################################

y_train <- train$Profit

y_test <- test$Profit

#############################################################
## PADRONIZAÇÃO
#############################################################

preproc <-
  
  preProcess(
    
    x_train,
    
    method=c(
      
      "center",
      
      "scale"
      
    )
    
  )

x_train_scaled <-
  
  predict(
    
    preproc,
    
    x_train
    
  )

x_test_scaled <-
  
  predict(
    
    preproc,
    
    x_test
    
  )

#############################################################
## VERIFICAÇÃO
#############################################################

dim(x_train_scaled)

dim(x_test_scaled)

#############################################################
## VALIDAÇÃO CRUZADA
#############################################################

ctrl <- trainControl(
  
  method="repeatedcv",
  
  number=10,
  
  repeats=5,
  
  savePredictions="final",
  
  returnResamp="all",
  
  allowParallel=TRUE,
  
  summaryFunction=defaultSummary
  
)

#############################################################
## PROCESSAMENTO PARALELO
#############################################################

nucleos <-
  
  parallel::detectCores()-1

cl <-
  
  makeCluster(nucleos)

registerDoParallel(cl)

cat("\n")

cat("Núcleos utilizados :",nucleos,"\n")

#############################################################
## EXPORTAÇÃO DOS OBJETOS
#############################################################

save(
  
  train,
  
  test,
  
  x_train,
  
  x_test,
  
  x_train_scaled,
  
  x_test_scaled,
  
  y_train,
  
  y_test,
  
  dummy,
  
  preproc,
  
  ctrl,
  
  file="Resultados/Objetos_ML.RData"
  
)

#############################################################
## RESUMO
#############################################################

cat("\n")

cat("-------------------------------------\n")

cat("Resumo da preparação\n")

cat("-------------------------------------\n")

cat("Observações totais :",nrow(dados_modelo),"\n")

cat("Treino :",nrow(train),"\n")

cat("Teste :",nrow(test),"\n")

cat("Preditoras :",ncol(x_train_scaled),"\n")

cat("-------------------------------------\n")

#############################################################
## TABELA DAS VARIÁVEIS
#############################################################

variaveis <-
  
  data.frame(
    
    Variavel=colnames(x_train_scaled)
    
  )

write.xlsx(
  
  variaveis,
  
  "Resultados/Tabelas/Variaveis_Modelagem.xlsx",
  
  overwrite=TRUE
  
)

#############################################################
## FINAL
#############################################################

cat("\n")

cat("SCRIPT 03 FINALIZADO\n")

#############################################################
## SCRIPT 04
## RANDOM FOREST
#############################################################

cat("\014")

#############################################################
## PACOTES
#############################################################

packages <- c(
  
  "randomForest",
  "caret",
  "vip",
  "ggplot2",
  "Metrics",
  "ranger",
  "openxlsx"
  
)

instalar <- packages[!(packages %in% installed.packages()[,1])]

if(length(instalar)>0){
  
  install.packages(instalar)
  
}

invisible(lapply(packages,
                 library,
                 character.only=TRUE))

#############################################################
## GRID DE HIPERPARÂMETROS
#############################################################

grid_rf <- expand.grid(
  
  mtry = 2:ncol(x_train_scaled),
  
  splitrule = c(
    "variance",
    "extratrees"
  ),
  
  min.node.size = c(
    1,
    3,
    5,
    10
  )
  
)

grid_rf

#############################################################
## TREINAMENTO
#############################################################

set.seed(2026)

modelo_rf <- train(
  
  x = x_train_scaled,
  
  y = y_train,
  
  method = "ranger",
  
  metric = "RMSE",
  
  trControl = ctrl,
  
  tuneGrid = grid_rf,
  
  num.trees = 1000,
  
  importance = "permutation"
  
)

#############################################################
## MELHOR MODELO
#############################################################

print(modelo_rf)

modelo_rf$bestTune

#############################################################
## PREDIÇÃO
#############################################################

pred_rf <- predict(
  
  modelo_rf,
  
  x_test_scaled
  
)

#############################################################
## IMPORTÂNCIA DAS VARIÁVEIS
#############################################################

imp_rf <- varImp(
  modelo_rf,
  scale = FALSE
)

print(imp_rf)

imp_export <- imp_rf$importance

imp_export$Variavel <- rownames(imp_export)

write.xlsx(
  
  imp_export,
  
  "Resultados/Tabelas/Importancia_RF.xlsx",
  
  overwrite=TRUE
  
)

#############################################################
## FIGURA IMPORTÂNCIA
#############################################################

imp_plot <- imp_rf$importance

imp_plot$Variavel <- rownames(imp_plot)

imp_plot <- imp_plot |>
  
  arrange(desc(Overall)) |>
  
  slice_head(n=20)

g1 <- ggplot(
  
  imp_plot,
  
  aes(
    
    reorder(Variavel, Overall),
    
    Overall
    
  )
  
)+
  
  geom_col(fill="steelblue")+
  
  coord_flip()+
  
  labs(
    
    x="",
    
    y="Importance",
    
    title="Random Forest",
    
    subtitle="Permutation Importance"
    
  )+
  
  theme_bw(base_size=14)

ggsave(
  
  "Resultados/Figuras/Importancia_RF.png",
  
  g1,
  
  width=8,
  
  height=6,
  
  dpi=600
  
)

#############################################################
## OBSERVADO VS PREDITO
#############################################################

dados_pred <- data.frame(
  
  Observado=y_test,
  
  Predito=pred_rf
  
)

g2 <- ggplot(
  
  dados_pred,
  
  aes(
    
    Observado,
    
    Predito
    
  )
  
)+
  
  geom_point(
    
    size=3,
    
    colour="steelblue"
    
  )+
  
  geom_abline(
    
    intercept=0,
    
    slope=1,
    
    colour="red",
    
    linewidth=1
    
  )+
  
  labs(
    
    x="Observed",
    
    y="Predicted"
    
  )+
  
  theme_bw()

ggsave(
  
  "Resultados/Figuras/RF_Observed_vs_Predicted.png",
  
  g2,
  
  width=6,
  
  height=6,
  
  dpi=600
  
)

#############################################################
## RESÍDUOS
#############################################################

dados_res <- data.frame(
  
  Predito=pred_rf,
  
  Residuo=y_test-pred_rf
  
)

g3 <- ggplot(
  
  dados_res,
  
  aes(
    
    Predito,
    
    Residuo
    
  )
  
)+
  
  geom_point(
    
    colour="darkgreen",
    
    size=3
    
  )+
  
  geom_hline(
    
    yintercept=0,
    
    linetype=2,
    
    colour="red"
    
  )+
  
  theme_bw()

ggsave(
  
  "Resultados/Figuras/RF_Residuals.png",
  
  g3,
  
  width=6,
  
  height=6,
  
  dpi=600
  
)

#############################################################
## RESAMPLE
#############################################################

png(
  
  "Resultados/Figuras/RF_Resampling.png",
  
  width=2200,
  
  height=1600,
  
  res=300
  
)

plot(modelo_rf)

dev.off()

#############################################################
## PREDIÇÕES
#############################################################

predicoes_rf <- data.frame(
  
  Observed=y_test,
  
  Predicted=pred_rf,
  
  Residual=y_test-pred_rf
  
)

write.xlsx(
  
  predicoes_rf,
  
  "Resultados/Tabelas/Predicoes_RF.xlsx",
  
  overwrite=TRUE
  
)

#############################################################
## SALVA MODELO
#############################################################

save(
  
  modelo_rf,
  
  file="Resultados/modelo_RF.RData"
  
)

#############################################################
## FINAL
#############################################################

cat("\n")

cat("----------------------------------------\n")

cat("Random Forest Finalizado\n")

cat("----------------------------------------\n")

#############################################################
## SCRIPT 05
## XGBOOST
#############################################################

cat("\014")

#############################################################
## PACOTES
#############################################################

packages <- c(
  
  "xgboost",
  "caret",
  "Metrics",
  "vip",
  "ggplot2",
  "openxlsx"
  
)

instalar <- packages[!(packages %in% installed.packages()[,1])]

if(length(instalar)>0){
  
  install.packages(instalar)
  
}

invisible(lapply(packages,
                 library,
                 character.only=TRUE))

#############################################################
## MATRIZES XGBOOST
#############################################################

dtrain <- xgb.DMatrix(
  data = as.matrix(x_train_scaled),
  label = y_train
)

dtest <- xgb.DMatrix(
  data = as.matrix(x_test_scaled),
  label = y_test
)

#############################################################
## PARÂMETROS
#############################################################

params <- list(
  
  objective = "reg:squarederror",
  
  eta = 0.05,
  
  max_depth = 3,
  
  subsample = 0.80,
  
  colsample_bytree = 0.80,
  
  min_child_weight = 1,
  
  gamma = 0,
  
  eval_metric = "rmse"
  
)

#############################################################
## VALIDAÇÃO CRUZADA
#############################################################

modelo_xgb <- xgb.train(
  
  params = params,
  
  data = dtrain,
  
  nrounds = 50,
  
  verbose = 0
  
)

#############################################################
## MELHOR MODELO
#############################################################

cat("Número de árvores: 50\n")

#############################################################
## PREDIÇÃO
#############################################################

pred_xgb <- predict(
  
  modelo_xgb,
  
  dtest
  
)

#############################################################
## IMPORTÂNCIA DAS VARIÁVEIS
#############################################################

imp_xgb <- xgb.importance(
  
  feature_names = colnames(x_train_scaled),
  
  model = modelo_xgb
  
)

imp_export <- imp_xgb

write.xlsx(
  
  imp_export,
  
  "Resultados/Tabelas/Importancia_XGBoost.xlsx",
  
  overwrite = TRUE
  
)

#############################################################
## FIGURA IMPORTÂNCIA
#############################################################

imp_plot <- imp_xgb |>
  
  rename(
    
    Variavel = Feature,
    
    Overall = Gain
    
  ) |>
  
  arrange(desc(Overall)) |>
  
  slice_head(n = 20)

g1 <- ggplot(
  
  imp_plot,
  
  aes(
    
    reorder(Variavel, Overall),
    
    Overall
    
  )
  
)+
  
  geom_col(fill="darkred")+
  
  coord_flip()+
  
  labs(
    
    x="",
    
    y="Importance",
    
    title="XGBoost",
    
    subtitle="Variable Importance"
    
  )+
  
  theme_bw(base_size=14)

ggsave(
  
  "Resultados/Figuras/Importancia_XGBoost.png",
  
  g1,
  
  width=8,
  
  height=6,
  
  dpi=600
  
)

#############################################################
## OBSERVADO VS PREDITO
#############################################################

dados_pred <- data.frame(
  
  Observado=y_test,
  
  Predito=pred_xgb
  
)

g2 <- ggplot(
  
  dados_pred,
  
  aes(
    
    Observado,
    
    Predito
    
  )
  
)+
  
  geom_point(
    
    colour="darkred",
    
    size=3
    
  )+
  
  geom_abline(
    
    intercept=0,
    
    slope=1,
    
    colour="blue",
    
    linewidth=1
    
  )+
  
  theme_bw()

ggsave(
  
  "Resultados/Figuras/XGB_Observed_vs_Predicted.png",
  
  g2,
  
  width=6,
  
  height=6,
  
  dpi=600
  
)

#############################################################
## RESÍDUOS
#############################################################

dados_res <- data.frame(
  
  Predito=pred_xgb,
  
  Residuo=y_test-pred_xgb
  
)

g3 <- ggplot(
  
  dados_res,
  
  aes(
    
    Predito,
    
    Residuo
    
  )
  
)+
  
  geom_point(
    
    colour="darkgreen",
    
    size=3
    
  )+
  
  geom_hline(
    
    yintercept=0,
    
    linetype=2,
    
    colour="red"
    
  )+
  
  theme_bw()

ggsave(
  
  "Resultados/Figuras/XGB_Residuals.png",
  
  g3,
  
  width=6,
  
  height=6,
  
  dpi=600
  
)

ggsave(
  "Resultados/Figuras/Importancia_XGBoost.png",
  g1,
  width = 8,
  height = 6,
  dpi = 600
)

#############################################################
## PREDIÇÕES
#############################################################

predicoes_xgb <- data.frame(
  
  Observed=y_test,
  
  Predicted=pred_xgb,
  
  Residual=y_test-pred_xgb
  
)

write.xlsx(
  
  predicoes_xgb,
  
  "Resultados/Tabelas/Predicoes_XGB.xlsx",
  
  overwrite=TRUE
  
)

#############################################################
## SALVA MODELO
#############################################################

save(
  
  modelo_xgb,
  
  file="Resultados/modelo_XGB.RData"
  
)

#############################################################
## FINAL
#############################################################

cat("--------------------------------------\n")

cat("XGBoost Finalizado\n")

cat("--------------------------------------\n")


#############################################################
## SCRIPT 06
## SUPPORT VECTOR MACHINE (SVM)
#############################################################

cat("\014")

#############################################################
## PACOTES
#############################################################

packages <- c(
  
  "caret",
  "e1071",
  "Metrics",
  "vip",
  "ggplot2",
  "openxlsx"
  
)

instalar <- packages[!(packages %in% installed.packages()[,1])]

if(length(instalar)>0){
  
  install.packages(instalar)
  
}

invisible(lapply(packages,
                 library,
                 character.only=TRUE))

#############################################################
## GRID DE HIPERPARÂMETROS
#############################################################

grid_svm <- expand.grid(
  
  sigma = c(
    0.001,
    0.005,
    0.010,
    0.050,
    0.100
  ),
  
  C = c(
    0.25,
    0.50,
    1,
    2,
    5,
    10,
    20,
    50
  )
  
)

grid_svm

#############################################################
## TREINAMENTO
#############################################################

set.seed(2026)

modelo_svm <- train(
  
  x = x_train_scaled,
  
  y = y_train,
  
  method = "svmRadial",
  
  metric = "RMSE",
  
  trControl = ctrl,
  
  tuneGrid = grid_svm
  
)

#############################################################
## MELHOR MODELO
#############################################################

print(modelo_svm)

modelo_svm$bestTune

#############################################################
## PREDIÇÕES
#############################################################

pred_svm <- predict(
  
  modelo_svm,
  
  x_test_scaled
  
)

#############################################################
## OBSERVADO VS PREDITO
#############################################################

dados_pred <- data.frame(
  
  Observado=y_test,
  
  Predito=pred_svm
  
)

g1 <- ggplot(
  
  dados_pred,
  
  aes(
    
    Observado,
    
    Predito
    
  )
  
)+
  
  geom_point(
    
    size=3,
    
    colour="steelblue"
    
  )+
  
  geom_abline(
    
    slope=1,
    
    intercept=0,
    
    colour="red",
    
    linewidth=1
    
  )+
  
  labs(
    
    x="Observed",
    
    y="Predicted"
    
  )+
  
  theme_bw()

ggsave(
  
  "Resultados/Figuras/SVM_Observed_vs_Predicted.png",
  
  g1,
  
  width=6,
  
  height=6,
  
  dpi=600
  
)

#############################################################
## RESÍDUOS
#############################################################

dados_res <- data.frame(
  
  Predito=pred_svm,
  
  Residuo=y_test-pred_svm
  
)

g2 <- ggplot(
  
  dados_res,
  
  aes(
    
    Predito,
    
    Residuo
    
  )
  
)+
  
  geom_point(
    
    size=3,
    
    colour="darkgreen"
    
  )+
  
  geom_hline(
    
    yintercept=0,
    
    linetype=2,
    
    colour="red"
    
  )+
  
  theme_bw()

ggsave(
  
  "Resultados/Figuras/SVM_Residuals.png",
  
  g2,
  
  width=6,
  
  height=6,
  
  dpi=600
  
)

#############################################################
## RESAMPLING
#############################################################

png(
  
  "Resultados/Figuras/SVM_Resampling.png",
  
  width=2200,
  
  height=1600,
  
  res=300
  
)

plot(modelo_svm)

dev.off()

#############################################################
## PREDIÇÕES
#############################################################

predicoes_svm <- data.frame(
  
  Observed = y_test,
  
  Predicted = pred_svm,
  
  Residual = y_test - pred_svm
  
)

write.xlsx(
  
  predicoes_svm,
  
  "Resultados/Tabelas/Predicoes_SVM.xlsx",
  
  overwrite=TRUE
  
)

#############################################################
## SALVA MODELO
#############################################################

save(
  
  modelo_svm,
  
  file="Resultados/modelo_SVM.RData"
  
)

#############################################################
## FINAL
#############################################################

cat("----------------------------------------\n")

cat("SUPPORT VECTOR MACHINE FINALIZADO\n")

cat("----------------------------------------\n")


#############################################################
## SCRIPT 07
## COMPARAÇÃO DOS MODELOS
#############################################################

cat("\014")

#############################################################
## PACOTES
#############################################################

packages <- c(
  
  "hydroGOF",
  "DescTools",
  "Metrics",
  "boot",
  "openxlsx",
  "dplyr"
  
)

instalar <- packages[!(packages %in% installed.packages()[,1])]

if(length(instalar)>0){
  
  install.packages(instalar)
  
}

invisible(lapply(packages,
                 library,
                 character.only=TRUE))

#############################################################
## PREDIÇÃO DA REGRESSÃO
#############################################################

pred_lm <- predict(
  
  modelo,
  
  newdata=test
  
)

#############################################################
## FUNÇÃO DE MÉTRICAS
#############################################################

calc_metrics <- function(obs,pred){
  
  RMSE <- sqrt(mean((obs-pred)^2))
  
  NRMSE <- RMSE/(max(obs)-min(obs))
  
  MAE <- mean(abs(obs-pred))
  
  MSE <- mean((obs-pred)^2)
  
  R2 <- caret::R2(pred, obs)
  
  MAPE <- mean(
    
    abs((obs-pred)/
          
          pmax(obs,1e-8))
    
  )*100
  
  RRMSE <- RMSE/mean(obs)*100
  
  NSE <- hydroGOF::NSE(pred,obs)
  
  Willmott <- hydroGOF::d(pred,obs)
  
  CCC <- DescTools::CCC(obs,pred)$rho.c[,1]
  
  Bias <- mean(pred-obs)
  
  Cor <- cor(
    obs,
    pred,
    use="complete.obs"
  )
  
  RPD <- sd(obs)/RMSE
  
  PBIAS <- 100*sum(pred-obs)/sum(obs)
  
  TaylorSkill <- (4*(1+cor(obs,pred)))/
    ((sd(pred)/sd(obs)+sd(obs)/sd(pred))^2*(1+1))
  
  data.frame(
    
    RMSE,
    
    MAE,
    
    MSE,
    
    R2,
    
    MAPE,
    
    RRMSE,
    
    NSE,
    
    Willmott,
    
    CCC,
    
    Bias,
    
    Cor,
    
    RPD,
    
    PBIAS,
    
    TaylorSkill
    
  )
  
}

#############################################################
## BOOTSTRAP DO RMSE
#############################################################

boot_rmse <- function(data, indices){
  
  d <- data[indices, ]
  
  sqrt(mean((d$obs - d$pred)^2))
  
}

bootstrap_ic <- function(obs, pred, modelo){
  
  dados_boot <- data.frame(
    obs = obs,
    pred = pred
  )
  
  boot_obj <- boot(
    data = dados_boot,
    statistic = boot_rmse,
    R = 1000
  )
  
  ic <- boot.ci(
    boot_obj,
    type = "perc"
  )
  
  data.frame(
    
    Modelo = modelo,
    
    RMSE = boot_obj$t0,
    
    IC95_inf = ic$percent[4],
    
    IC95_sup = ic$percent[5]
    
  )
  
}

#############################################################
## MÉTRICAS
#############################################################

met_lm <- calc_metrics(y_test,pred_lm)

met_rf <- calc_metrics(y_test,pred_rf)

met_xgb <- calc_metrics(y_test,pred_xgb)

met_svm <- calc_metrics(y_test,pred_svm)

#############################################################
## TABELA FINAL
#############################################################

resultado <- bind_rows(
  
  cbind(Model="Linear Regression",met_lm),
  
  cbind(Model="Random Forest",met_rf),
  
  cbind(Model="XGBoost",met_xgb),
  
  cbind(Model="SVM",met_svm)
  
)

resultado

#############################################################
## INTERVALO DE CONFIANÇA DO RMSE
#############################################################

ic_rmse <- bind_rows(
  
  bootstrap_ic(
    y_test,
    pred_lm,
    "Linear Regression"
  ),
  
  bootstrap_ic(
    y_test,
    pred_rf,
    "Random Forest"
  ),
  
  bootstrap_ic(
    y_test,
    pred_xgb,
    "XGBoost"
  ),
  
  bootstrap_ic(
    y_test,
    pred_svm,
    "SVM"
  )
  
)

ic_rmse

#############################################################
## RANKING
#############################################################

ranking <- resultado |>
  
  arrange(
    
    RMSE
    
  )

ranking

#############################################################
## EXPORTAÇÃO
#############################################################

write.xlsx(
  
  resultado,
  
  "Resultados/Tabelas/Comparacao_Modelos.xlsx",
  
  overwrite=TRUE
  
)

write.xlsx(
  
  ranking,
  
  "Resultados/Tabelas/Ranking_Modelos.xlsx",
  
  overwrite=TRUE
  
)

write.xlsx(
  
  ic_rmse,
  
  "Resultados/Tabelas/IC95_RMSE.xlsx",
  
  overwrite = TRUE
  
)

#############################################################
## MELHOR MODELO
#############################################################

melhor <- ranking$Model[1]

cat("\n")

cat("-------------------------------------\n")

cat("Melhor modelo:",melhor,"\n")

cat("-------------------------------------\n")

#############################################################
## TABELA FORMATADA
#############################################################

resultado_formatado <- resultado

resultado_formatado[,-1] <-
  
  round(
    
    resultado_formatado[,-1],
    
    4
    
  )

resultado_formatado

#############################################################
## EXPORTAÇÃO CSV
#############################################################

write.csv(
  
  resultado_formatado,
  
  "Resultados/Tabelas/Comparacao_Modelos.csv",
  
  row.names=FALSE
  
)

#############################################################
## SALVA OBJETOS
#############################################################

save(
  
  resultado,
  
  ranking,
  
  pred_lm,
  
  pred_rf,
  
  pred_xgb,
  
  pred_svm,
  
  file="Resultados/Metricas_Modelos.RData"
  
)

#############################################################
## ENCERRA CLUSTER
#############################################################

stopCluster(cl)

registerDoSEQ()

#############################################################
## FINAL
#############################################################

cat("\n")

cat("SCRIPT 07 FINALIZADO\n")

#############################################################
## SCRIPT 08
## FIGURAS FINAIS
#############################################################

cat("\014")

#############################################################
## PACOTES
#############################################################

packages <- c(
  
  "ggplot2",
  "tidyr",
  "dplyr",
  "openxlsx",
  "pheatmap",
  "fmsb",
  "plotrix",
  "patchwork",
  "viridis"
  
)

instalar <- packages[!(packages %in% installed.packages()[,1])]

if(length(instalar)>0){
  
  install.packages(instalar)
  
}

invisible(lapply(packages,
                 library,
                 character.only=TRUE))

#############################################################
## CARREGA RESULTADOS
#############################################################

resultado <- read.xlsx(
  
  "Resultados/Tabelas/Comparacao_Modelos.xlsx"
  
)

#############################################################
## 1) RANKING RMSE
#############################################################

ranking_rmse <- resultado |>
  
  arrange(RMSE)

g1 <- ggplot(
  
  ranking_rmse,
  
  aes(
    
    reorder(Model,RMSE),
    
    RMSE,
    
    fill=Model
    
  )
  
)+
  
  geom_col(width=.70)+
  
  coord_flip()+
  
  theme_bw(base_size=14)+
  
  theme(
    
    legend.position="none"
    
  )+
  
  labs(
    
    x="",
    
    y="RMSE"
    
  )

ggsave(
  
  "Resultados/Figuras/Fig01_Ranking_RMSE.png",
  
  g1,
  
  width=7,
  
  height=5,
  
  dpi=600
  
)

#############################################################
## 2) R²
#############################################################

g2 <- ggplot(
  
  resultado,
  
  aes(
    
    reorder(Model,R2),
    
    R2,
    
    fill=Model
    
  )
  
)+
  
  geom_col(width=.70)+
  
  coord_flip()+
  
  theme_bw(base_size=14)+
  
  theme(
    
    legend.position="none"
    
  )

ggsave(
  
  "Resultados/Figuras/Fig02_R2.png",
  
  g2,
  
  width=7,
  
  height=5,
  
  dpi=600
  
)

#############################################################
## 3) HEATMAP
#############################################################

heat <- resultado |>
  
  select(
    
    RMSE,
    MAE,
    MAPE,
    R2,
    NSE,
    Willmott,
    CCC,
    TaylorSkill
    
  )

rownames(heat) <- resultado$Model

heat$RMSE <- -heat$RMSE

heat$MAE <- -heat$MAE

heat$MAPE <- -heat$MAPE

heat <- as.data.frame(scale(heat))

png(
  
  "Resultados/Figuras/Fig03_Heatmap.png",
  
  width=2600,
  
  height=2200,
  
  res=600
  
)

pheatmap(
  
  heat,
  
  cluster_rows=FALSE,
  
  cluster_cols=FALSE,
  
  fontsize=12
  
)

dev.off()

#############################################################
## 4) RADAR CHART
#############################################################

radar <- resultado |>

  select(

    RMSE,
    MAE,
    R2,
    NSE,
    CCC,
    TaylorSkill

  )

#############################################################
## NORMALIZAÇÃO DAS MÉTRICAS
#############################################################

radar_norm <- radar

## Métricas em que MENOR é melhor
radar_norm$RMSE <-
  1 - (radar$RMSE - min(radar$RMSE)) /
  (max(radar$RMSE) - min(radar$RMSE))

radar_norm$MAE <-
  1 - (radar$MAE - min(radar$MAE)) /
  (max(radar$MAE) - min(radar$MAE))

## Métricas em que MAIOR é melhor
radar_norm$R2 <-
  (radar$R2 - min(radar$R2)) /
  (max(radar$R2) - min(radar$R2))

radar_norm$NSE <-
  (radar$NSE - min(radar$NSE)) /
  (max(radar$NSE) - min(radar$NSE))

radar_norm$CCC <-
  (radar$CCC - min(radar$CCC)) /
  (max(radar$CCC) - min(radar$CCC))

radar_norm$TaylorSkill <-
  (radar$TaylorSkill - min(radar$TaylorSkill)) /
  (max(radar$TaylorSkill) - min(radar$TaylorSkill))

#############################################################
## PREPARAÇÃO
#############################################################

radar_final <- rbind(

  rep(1, ncol(radar_norm)),

  rep(0, ncol(radar_norm)),

  radar_norm

)

rownames(radar_final) <- c(

  "max",

  "min",

  resultado$Model

)

#############################################################
## FIGURA
#############################################################

png(

  "Resultados/Figuras/Fig04_Radar.png",

  width = 2400,

  height = 2400,

  res = 600

)

radarchart(

  radar_final,

  axistype = 1,

  pcol = 1:4,

  plwd = 3,

  cglcol = "grey"

)

legend(

  "topright",

  legend = resultado$Model,

  col = 1:4,

  lwd = 3,

  bty = "n"

)

dev.off()

#############################################################
## 5) OBSERVADO VS PREDITO
#############################################################

predicoes <- bind_rows(
  
  data.frame(
    
    Modelo="Linear",
    
    Observado=y_test,
    
    Predito=pred_lm
    
  ),
  
  data.frame(
    
    Modelo="RF",
    
    Observado=y_test,
    
    Predito=pred_rf
    
  ),
  
  data.frame(
    
    Modelo="XGBoost",
    
    Observado=y_test,
    
    Predito=pred_xgb
    
  ),
  
  data.frame(
    
    Modelo="SVM",
    
    Observado=y_test,
    
    Predito=pred_svm
    
  )
  
)

g5 <- ggplot(
  
  predicoes,
  
  aes(
    
    Observado,
    
    Predito
    
  )
  
)+
  
  geom_point(
    
    colour="steelblue",
    
    size=2
    
  )+
  
  geom_abline(
    
    slope=1,
    
    intercept=0,
    
    colour="red"
    
  )+
  
  facet_wrap(
    
    ~Modelo
    
  )+
  
  theme_bw()

ggsave(
  
  "Resultados/Figuras/Fig05_Observed_vs_Predicted.png",
  
  g5,
  
  width=10,
  
  height=8,
  
  dpi=600
  
)


#############################################################
## 6) RESÍDUOS
#############################################################

predicoes$Residuo <-
  
  predicoes$Observado-
  
  predicoes$Predito

g6 <- ggplot(
  
  predicoes,
  
  aes(
    
    Predito,
    
    Residuo
    
  )
  
)+
  
  geom_point(
    
    colour="darkgreen"
    
  )+
  
  geom_hline(
    
    yintercept=0,
    
    colour="red",
    
    linetype=2
    
  )+
  
  facet_wrap(
    
    ~Modelo
    
  )+
  
  theme_bw()

ggsave(
  
  "Resultados/Figuras/Fig06_Residuals.png",
  
  g6,
  
  width=10,
  
  height=8,
  
  dpi=600
  
)

#############################################################
## 7) IMPORTÂNCIA RF X XGB
#############################################################

rf_imp <- read.xlsx(
  
  "Resultados/Tabelas/Importancia_RF.xlsx"
  
)

xgb_imp <- read.xlsx(
  
  "Resultados/Tabelas/Importancia_XGBoost.xlsx"
  
)

rf_imp$Modelo <- "Random Forest"

xgb_imp$Modelo <- "XGBoost"

imp <- bind_rows(
  
  rf_imp,
  
  xgb_imp
  
)


g7 <- ggplot(
  
  imp,
  
  aes(
    
    reorder(Variavel, Overall),
    
    Overall,
    
    fill = Modelo
    
  )
  
)+
  
  geom_col(width = 0.75)+
  
  coord_flip()+
  
  facet_wrap(
    ~Modelo,
    scales = "free_y"
  )+
  
  labs(
    
    x = "",
    
    y = "Variable importance"
    
  )+
  
  theme_bw(base_size = 14)+
  
  theme(
    
    legend.position = "none",
    
    strip.text = element_text(face = "bold")
    
  )

ggsave(
  
  "Resultados/Figuras/Fig07_Importance.png",
  
  g7,
  
  width=10,
  
  height=8,
  
  dpi=600
  
)

#############################################################
## 8) TAYLOR DIAGRAM
#############################################################

png(
  
  "Resultados/Figuras/Fig08_Taylor.png",
  
  width=2400,
  
  height=2400,
  
  res=600
  
)

plotrix::taylor.diagram(
  
  y_test,
  
  pred_lm,
  
  pch=19,
  
  col="black"
  
)

plotrix::taylor.diagram(
  
  y_test,
  
  pred_rf,
  
  add=TRUE,
  
  pch=19,
  
  col="blue"
  
)

plotrix::taylor.diagram(
  
  y_test,
  
  pred_xgb,
  
  add=TRUE,
  
  pch=19,
  
  col="red"
  
)

plotrix::taylor.diagram(
  
  y_test,
  
  pred_svm,
  
  add=TRUE,
  
  pch=19,
  
  col="darkgreen"
  
)

legend(
  
  "topright",
  
  legend=c(
    
    "LM",
    
    "RF",
    
    "XGB",
    
    "SVM"
    
  ),
  
  pch=19,
  
  col=c(
    
    "black",
    
    "blue",
    
    "red",
    
    "darkgreen"
    
  ),
  
  bty="n"
  
)

dev.off()

#############################################################
## FINAL
#############################################################

cat("--------------------------------------\n")

cat("TODAS AS FIGURAS GERADAS\n")

cat("--------------------------------------\n")
