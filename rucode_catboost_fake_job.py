# -*- coding: utf-8 -*-
"""RuCode_catboost_fake_job.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1XYPSqbjHbmeEIxGMP0yZpMkgQKIBozFN
"""

!pip install catboost

"""Baseline for https://www.kaggle.com/c/rucode-fake-job-postings/
It detects fake job ads.
Made by Alex Bocharov skype bam271074
CatBoost version catboost-0.24.1
"""

#baseline to take part in RuCode contest 2020
import numpy as np
import pandas as pd
from catboost import Pool, CatBoostClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
RS=42
import re
import nltk
from nltk import tokenize
nltk.download('punkt')
from nltk.corpus import stopwords
nltk.download('stopwords')
from nltk.stem import WordNetLemmatizer
nltk.download('wordnet')
stop_words = set(stopwords.words('english'))

"""Метрика оценивания в этом соревновании — Mean F1-Score. Метрика F1 score оценивает точность бинарной классификации, используя величины точность p и полноту r. Точность (precision)— это отношение true positives (tp, объектов, истинный ответ которых 1 и предсказание алгоритма для них тоже 1) к количеству всех объектов, для которых алгоритм выдал ответ 1 (tp + fp). Полнота (recall) — это отношение true positives к количеству всех объектов, истинный ответ которых есть 1 (tp + fn). F1 score вычисляется как:

F1=2p⋅rp+r  where  p=tptp+fp,  r=tptp+fn
F1 metric одинаково учитывает точность и полноту. Поэтому алгоритм, у которого хорошая точность, но плохая полнота или наоборот, будет иметь низкий F1 score.

Более подробно про метрику F1 читайте по ссылке: https://en.wikipedia.org/wiki/F1_score

Формат ответа
Для каждого Id в тестовом датасете, файл ответа должен содержать 1 величину: Ответ, фейковое это объявление или нет, в виде 0 или 1
"""

# подключаем гугл диск на котором данные
from google.colab import drive
drive.mount ('/content/gdrive', force_remount = True)

!ls /content/gdrive/'My Drive'/rucode_fake_job

#let s load data
df_train=pd.read_csv('../content/gdrive/My Drive/rucode_fake_job/train_data.csv',index_col='Id',encoding='utf-8')
df_train.head()

df_train.shape

df_train.describe(include='object').T

#let s see how many NaNs
df_train.isnull().sum()

df_train['Зарплата'].fillna(value='-40000',inplace=True)  #inplace=True обновляет значения в датафрейме
df_train['Место'].fillna(value='UnknownPlace',inplace=True)
df_train['Описание компании'].fillna(value='UnknownCompany',inplace=True)
df_train['Позиция'].fillna(value='UnknownPosition',inplace=True)  #inplace=True обновляет значения в датафрейме
df_train['Индустрия'].fillna(value='UnknownInductry',inplace=True)

#let s see how many NaNs after we fill some NaNs
df_train.isnull().sum()

TOKEN_RE = re.compile(r'[\w\d]+')  #regular expression to start with
#tokenizer=WordPunctTokenizer()  #regular expr is better

def str_to_int(txt):
  """convert str of Salary into int """
  all_tokens = TOKEN_RE.findall(txt)
  s=all_tokens[0]
  if s == 'Oct':
    s='-1111'
  if s == 'Dec':
    s='-2222'    
  if s == 'Jun':
    s='-3333'     
  return str(s)

str_to_int('23-34')

df_train['Зарплата']=df_train['Зарплата'].apply(str_to_int)

def tokenize_text_simple_regex(txt, min_token_size=2):
    """ This func tokenize text with TOKEN_RE applied ealier """
    txt = txt.lower()
    all_tokens = TOKEN_RE.findall(txt)
    #all_tokens=tokenizer.tokenize(txt)
    all_tokens = [token for token in all_tokens if len(token) >= min_token_size]
    all_tokens = [w for w in all_tokens if not w in stop_words]  #del stop words
    s=' '.join(all_tokens)
    return s

tokenize_text_simple_regex('I am very bad boy and cats are oftern kitty...')

#classes unbalanced so we will use class_weights=balanced
df_train['Фейк'].value_counts()

#let s read test data
df_test=pd.read_csv('../content/gdrive/My Drive/rucode_fake_job/test_data.csv',index_col='Id')
df_test.head()

df_test.shape

df_test['Зарплата'].fillna(value='-40000',inplace=True)  #inplace=True обновляет значения в датафрейме
df_test['Место'].fillna(value='UnknownPlace',inplace=True)
df_test['Описание компании'].fillna(value='UnknownCompany',inplace=True)
df_test['Позиция'].fillna(value='UnknownPosition',inplace=True)  #inplace=True обновляет значения в датафрейме
df_test['Индустрия'].fillna(value='UnknownIndustry',inplace=True)
df_test['Зарплата']=df_test['Зарплата'].apply(str_to_int)

def concat_features(x,y,z,a,b,c,d,i,f,j,h,k,l,m,n):
  """
  Let s concat feature in order to make tfidf later
  """
  buff=(str(x)+' '+str(y)+' '+str(z)+' '+str(a)+' '+str(b)+' '+str(c)+' '+str(d)+' '+str(i)+' '+str(f)+
        ' '+str(j)+' '+str(h)+' '+str(k)+' '+str(l)+' '+str(m)+' '+str(n))
  return buff

concat_features('Apple','I ','do','23','k', 'like', 'this', 'phone','we','da','ss,','df','ff','e','g')

X_tr=[]  #list for concat results
#loop on dataframe
for t in df_train.itertuples():
  buff=concat_features(t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],t[10],t[11],t[12],t[13],t[14],t[15])
  buff=tokenize_text_simple_regex(buff, min_token_size=1)
  X_tr.append(buff)

X_tr[0]

df_train['text']=X_tr

sequence_lengths = df_train.text.apply(len)

sequence_lengths.describe()

df_train['len']=sequence_lengths

#let add data from test in order to vectorize
X_t=[]
for t in df_test.itertuples():
  buff=concat_features(t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],t[10],t[11],t[12],t[13],t[14],t[15])
  buff=tokenize_text_simple_regex(buff, min_token_size=1)
  X_t.append(buff)

df_test['text']=X_t

sequence_len = df_test.text.apply(len)
df_test['len']=sequence_len

X_features=['text','len']

#divide dataset to train and test

X_train, X_test, y_train, y_test=train_test_split(df_train[X_features],
                                                  df_train[['Фейк']], shuffle = True,
                                                test_size=0.2,random_state=RS)

def f1_eval(y_pred, dtrain):
    y_true = dtrain.get_label()
    err = 1-f1_score(y_true, np.round(y_pred))
    return 'f1_err', err

target_col = 'Фейк'
text_cols = ['text']
categorical_cols = []

train_pool = Pool(
        X_train, 
        y_train, 
        cat_features=categorical_cols,
        text_features=text_cols,
        feature_names=X_features,
    )
    valid_pool = Pool(
        X_test, 
        y_test, 
        cat_features=categorical_cols,
        text_features=text_cols,
        feature_names=X_features,
    )

clf=CatBoostClassifier(iterations= 1100,
    #auto_class_weights='Balanced',
    #custom_metric='F1',
    #l2_leaf_reg=10,
    learning_rate= 0.02,
    depth=14,
    eval_metric= 'Logloss',
    #eval_metric='F1',
    task_type= 'GPU',
    early_stopping_rounds= 100,
    #class_weights=[0.95,0.05],
    use_best_model= True,
    random_seed=RS,
    verbose= 10
)
#clf=CatBoostClassifier(iterations=300, random_seed=RS,learning_rate=0.1,
#                       class_weights='balanced',task_type="GPU",eval_metric=f1_score)

clf.fit(train_pool, eval_set=valid_pool,plot=True)
#clf.fit(X_train,y_train,cat_features=categorical_cols,text_features=text_cols)

print('Правильность на обучающей выборке: {:.4f}'.format(clf.score(X_train,y_train)))

print('Правильность на валидационной выборке: {:.4f}'.format(clf.score(X_test,y_test)))

clf.feature_importances_

y_pred=clf.predict(X_test)
print(y_pred[:10])

print('Метрика ф1 на валидационной выборке: {:.4f}'.format(f1_score(y_pred,y_test)))

y_out=clf.predict(df_test[X_features])
print(y_out[0])

len(y_out)

df_test['Фейк']=y_out
df_test.tail()

#let s save our prediction

df_test['Фейк'].to_csv('submission.csv',header=True,index=True)

!ls

from google.colab import files

files.download('submission.csv')

#0.83817



