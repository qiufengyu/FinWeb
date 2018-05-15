import jieba
import numpy as np

from scipy.spatial.distance import cosine
from rest_framework.views import APIView
from app.db.mongo import MongoUser, MongoNews
from app.recommend.wordvec import WordVec

from rest_framework.response import Response

db_users = MongoUser()
db_news = MongoNews()

class GetRecommend(APIView):
  def __init__(self, dim=128):
    self.authentication_classes = []
    self.permission_classes = []
    self.word_vec = WordVec()
    self.dim = dim

  def _get_title_vec(self, title: str):
    item_matrix = []
    for token in jieba.cut(title, cut_all=False):
      token_vec = self.word_vec.getvec(token)
      if token_vec is not None:
        item_matrix.append(token_vec)
    item_array = np.array(item_matrix)
    return (np.mean(item_array, axis=0), np.max(item_array, axis=0))

  def get(self, request, format=None):
    print(request.GET)
    username = request.GET.get('username', None)
    user_embedding_matrix = []
    candidates = db_news.get_latest_news(top=100)
    for candidate in candidates:
      candidate['score'] = candidate['reads'] / 1000.0
    if username:
      user_read_list = db_users.get_user_recent_reads(username)
      if len(user_read_list) < 1:
        user_embedding_matrix.append([0.0] * self.dim)
      else:
        for read in user_read_list:
          user_embedding_matrix.append(self._get_title_vec(read)[0])
      user_embedding_array = np.array(user_embedding_matrix)
      user_em_mean = np.mean(user_embedding_array, axis=0)
      user_em_max = np.max(user_embedding_array, axis=0)
      user_em = np.concatenate((user_em_mean, user_em_max), axis=0)
      if len(user_read_list) > 1:
        for candidate in candidates:
          candidate_title = candidate['title']
          candidate_temp = self._get_title_vec(candidate_title)
          candidate_em = np.concatenate((candidate_temp[0], candidate_temp[1]), axis=0)
          candidate['score'] += 1.0 - cosine(user_em, candidate_em)

    data = sorted(candidates, key=lambda x: x['score'], reverse=True)
    return Response(data)


if __name__ == '__main__':
  gr = GetRecommend()
  gr.get(None)





