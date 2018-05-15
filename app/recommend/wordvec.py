import gensim
from django.conf import settings

class WordVec(object):
  def __init__(self, dim=128):
    self.model_name = settings.WORD_VEC_MODEL
    self.model = None
    self.dim = dim

  def getvec(self, word: str):
    if not self.model:
      self.model = gensim.models.Word2Vec.load(self.model_name)
    if word in self.model.wv:
      return self.model.wv[word]
    else:
      return None






