library(readr)
library(readxl)

library(readr)

saude1996 <- read_delim(
  "saude1996.csv",
  delim = "\t",
  locale = locale(encoding = "UTF-8"),
  show_col_types = FALSE
)

unique(saude1996$def_tipo_obito)
dim(saude1996)
names(saude1996)
View(saude1996)

head(saude1996)
tail(saude1996)
class(saude1996)
str(saude1996)
summary(saude1996)

amostra1 <- saude1996[sample(nrow(saude1996), 100), ] # amostra com n=100 registros
head(amostra1) #lendo os dados da amostra
View(amostra1) #lendo os dados da amostra no formato de tabela

install.packages("TeachingSampling")
library(TeachingSampling)

set.seed(123)

amostra2 <- saude1996 |>
  dplyr::slice_sample(prop = 0.10) # amostra com p=10% => n=3000

# Se a ideia for fazer amostragem estratificada, por exemplo, pela variável dia_semana_obito, você pode fazer

library(dplyr)

set.seed(123)

amostra2 <- saude1996 |>
  group_by(dia_semana_obito) |>
  slice_sample(prop = 0.10) |>
  ungroup()


nrow(amostra2)
View(amostra2)

#Amostragem sistemática

set.seed(123)

N <- nrow(saude1996)
r <- 3

inicio <- sample(1:r, size = 1)

posicoes <- seq(from = inicio, to = N, by = r)

amostra_sis <- saude1996[posicoes, ]

nrow(amostra_sis)
View(amostra_sis)

#Se você quiser aplicar apenas à variável def_est_civil, como tentou no código:

set.seed(123)

N <- length(saude1996$def_est_civil)
r <- 3

inicio <- sample(1:r, size = 1)

posicoes <- seq(from = inicio, to = N, by = r)

amostra_sis_est_civil <- saude1996$def_est_civil[posicoes]

#Se a sua intenção era tirar uma amostra com n = 3000, o intervalo sistemático deve ser calculado assim:

set.seed(123)

N <- nrow(saude1996)
n <- 3000

r <- floor(N / n)

inicio <- sample(1:r, size = 1)

posicoes <- seq(from = inicio, to = N, by = r)

amostra_sistematica <- saude1996[posicoes, ]

amostra_sistematica <- amostra_sistematica[1:n, ]

nrow(amostra_sistematica)
View(amostra_sistematica)
