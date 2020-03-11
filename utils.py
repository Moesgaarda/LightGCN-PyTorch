'''
Created on Mar 1, 2020
Pytorch Implementation of LightGCN in
Xiangnan He et al. LightGCN: Simplifying and Powering Graph Convolution Network for Recommendation

@author: Jianbai Ye (gusye@mail.ustc.edu.cn)
'''
import world
import torch
from torch import nn, optim
import numpy as np
from torch import log
from dataloader import BasicDataset
from time import time
from model import LightGCN
import random

        
class BPRLoss:
    def __init__(self, recmodel,config):
        recmodel : LightGCN
        self.model = recmodel
        self.f = nn.Sigmoid()
        self.weight_decay = config['decay']
        self.lr = config['lr']
        self.opt = optim.Adam(recmodel.parameters(), lr=self.lr)
        
        
    def stageOne(self, users, pos, neg):
        users_emb ,pos_emb, neg_emb = self.model.getEmbedding(users, pos, neg)
        # print(users_emb.dtype,pos_emb.dtype, neg_emb.dtype)
        reg_loss = (1/2)*self.weight_decay*(torch.norm(users_emb, 2) + torch.norm(pos_emb, 2) + torch.norm(neg_emb, 2))
        reg_loss = reg_loss/float(len(users_emb))
        
        
        pos_scores = torch.mul(users_emb, pos_esmb)
        pos_scores = torch.sum(pos_scores, dim=1)
        # print('pos:', pos_scores[:5])
        neg_scores = torch.mul(users_emb, neg_emb)
        neg_scores = torch.sum(neg_scores, dim=1)
        # print('neg:', neg_scores[:5])
        '''
        bpr  = self.f(pos_scores - neg_scores)
        bpr  = -torch.log(bpr)
        loss = torch.mean(bpr)
        '''
        loss = torch.mean(torch.nn.functional.softplus(-(pos_scores - neg_scores)))
        loss = loss + reg_loss
        
        self.opt.zero_grad()
        loss.backward()
        self.opt.step()
        
        return loss.cpu().item()



def __UniformSample(users, dataset, k=1):
    """
    uniformsample k negative items and one positive item for one user
    return:
        np.array
    """
    dataset : BasicDataset
    allPos   = dataset.getUserPosItems(users)
    allNeg   = dataset.getUserNegItems(users)
    # allItems = list(range(dataset.m_items))
    S = []
    sample_time1 = 0.
    sample_time2 = 0.
    total_start = time()
    for i, user in enumerate(users):
        start = time()
        posForUser = allPos[i]
        # negForUser = dataset.getUserNegItems([user])[0]
        negForUser = allNeg[i]
        sample_time2 += time()-start
        
        start = time()
        onePos_index = np.random.randint(0, len(posForUser))
        onePos     = posForUser[onePos_index:onePos_index+1]
        # onePos     = np.random.choice(posForUser, size=(1, ))
        kNeg_index = np.random.randint(0, len(negForUser), size=(k, ))
        kNeg       = negForUser[kNeg_index]
        end = time()
        sample_time1 += end-start
        S.append(np.hstack([onePos, kNeg]))
    total = time() - total_start
    return np.array(S), [total, sample_time1, sample_time2]
        

def UniformSample_allpos_largeDataset(users, dataset, k=4):
    """
    uniformsample k negative items and one positive item for one user
    return:
        np.array
    """
    dataset : BasicDataset
    allPos   = dataset.getUserPosItems(users)
    # allNeg   = dataset.getUserNegItems(users)
    # allItems = list(range(dataset.m_items))
    S = []
    sample_time1 = 0.
    sample_time2 = 0.
    total_start = time()
    for i, user in enumerate(users):
        start = time()
        posForUser = allPos[i]
        # negForUser = dataset.getUserNegItems([user])[0]
        negForUser_len = dataset.m_items - len(posForUser)
        sample_time2 += time()-start
        
        for positem in posForUser:
            start = time()
            # onePos_index = np.random.randint(0, len(posForUser))
            # onePos     = posForUser[onePos_index:onePos_index+1]
            # onePos     = np.random.choice(posForUser, size=(1, ))
            # kNeg_index = np.random.randint(0, len(negForUser), size=(k, ))
            # kNeg       = negForUser[kNeg_index]
            kNeg = []
            neg_i = 0
            while True:
                if neg_i == k:
                    break
                neg = np.random.randint(0, negForUser_len)
                if neg in posForUser:
                    continue
                else:
                    kNeg.append(neg)
                    neg_i += 1
            end = time()
            sample_time1 += end-start
            for negitemForpos in kNeg:
                S.append([user, positem, negitemForpos])
            # S.append(np.hstack([onePos, kNeg]))
    total = time() - total_start
    return np.array(S), [total, sample_time1, sample_time2]

def UniformSample_original(users, dataset):
    """
    the original impliment of BPR Sampling in LightGCN
    :return:
        np.array
    """
    dataset : BasicDataset
    allPos = dataset.getUserPosItems(users)
    S = []
    sample_time1 = 0.
    sample_time2 = 0.
    total_start = time()
    for i, user in enumerate(users):
        start = time()
        posForUser = list(allPos[i])
        if len(posForUser) == 0:
            continue
        sample_time2 += time() - start
        positem = np.array(random.sample(posForUser, 1)[0])
        while True:
            negitem = np.random.randint(0, dataset.m_items)
            if negitem in posForUser:
                continue
            else:
                break
        S.append([user, positem, negitem])
        end = time()
        sample_time1 += end - start
    total = time() - total_start
    return np.array(S), [total, sample_time1, sample_time2]



def UniformSample_allpos(users, dataset, k=4):
    """
    uniformsample k negative items and one positive item for one user
    return:
        np.array
    """
    dataset : BasicDataset
    allPos   = dataset.getUserPosItems(users)
    allNeg   = dataset.getUserNegItems(users)
    # allItems = list(range(dataset.m_items))
    S = []
    sample_time1 = 0.
    sample_time2 = 0.
    total_start = time()
    for i, user in enumerate(users):
        start = time()
        posForUser = allPos[i]
        # negForUser = dataset.getUserNegItems([user])[0]
        negForUser = allNeg[i]
        sample_time2 += time()-start
        
        for positem in posForUser:
            start = time()
            # onePos_index = np.random.randint(0, len(posForUser))
            # onePos     = posForUser[onePos_index:onePos_index+1]
            # onePos     = np.random.choice(posForUser, size=(1, ))
            kNeg_index = np.random.randint(0, len(negForUser), size=(k, ))
            kNeg       = negForUser[kNeg_index]
            end = time()
            sample_time1 += end-start
            for negitemForpos in kNeg:
                S.append([user, positem, negitemForpos])
            # S.append(np.hstack([onePos, kNeg]))
    total = time() - total_start
    return np.array(S), [total, sample_time1, sample_time2]
        

def getAllData(dataset, gamma=None):
    """
    return all data (n_users X m_items)
    return:
        [u, i, x_ui]
    """
    # if gamma is not None:
    #     print(gamma.size())
    dataset : BasicDataset
    users = []
    items = []
    xijs   = None
    allPos = dataset.allPos
    allxijs = np.array(dataset.UserItemNet.todense()).reshape(-1)
    items = np.tile(np.arange(dataset.m_items), (1, dataset.n_users)).squeeze()
    users = np.tile(np.arange(dataset.n_users), (dataset.m_items,1)).T.reshape(-1)
    print(len(allxijs), len(items), len(users))
    assert len(allxijs) == len(items) == len(users)
    # for user in range(dataset.n_users):
    #     users.extend([user]*dataset.m_items)
    #     items.extend(range(dataset.m_items))
    if gamma is not None:
        return torch.Tensor(users).long(), torch.Tensor(items).long(), torch.from_numpy(allxijs).long(), gamma.reshape(-1)
    return torch.Tensor(users).long(), torch.Tensor(items).long(), torch.from_numpy(allxijs).long()
# ===================end samplers==========================
# =========================================================


def minibatch(*tensors, **kwargs):

    batch_size = kwargs.get('batch_size', world.config['bpr_batch_size'])

    if len(tensors) == 1:
        tensor = tensors[0]
        for i in range(0, len(tensor), batch_size):
            yield tensor[i:i + batch_size]
    else:
        for i in range(0, len(tensors[0]), batch_size):
            yield tuple(x[i:i + batch_size] for x in tensors)


def shuffle(*arrays, **kwargs):

    require_indices = kwargs.get('indices', False)

    if len(set(len(x) for x in arrays)) != 1:
        raise ValueError('All inputs to shuffle must have '
                         'the same length.')

    shuffle_indices = np.arange(len(arrays[0]))
    np.random.shuffle(shuffle_indices)

    if len(arrays) == 1:
        result = arrays[0][shuffle_indices]
    else:
        result = tuple(x[shuffle_indices] for x in arrays)

    if require_indices:
        return result, shuffle_indices
    else:
        return result

# ====================Metrics==============================
# =========================================================
def RecallPrecision_ATk(test_data, r, k):
    """
    test_data should be a list? cause users may have different amount of pos items. shape (test_batch, k)
    pred_data : shape (test_batch, k) NOTE: pred_data should be pre-sorted
    k : top-k
    """
    right_pred = r[:, :k].sum(1)
    precis_n = k
    recall_n = np.array([len(test_data[i]) for i in range(len(test_data))])
    recall = np.sum(right_pred/recall_n)
    precis = np.sum(right_pred)/precis_n
    return {'recall': recall, 'precision': precis}


def MRRatK_r(r, k):
    """
    Mean Reciprocal Rank
    """
    pred_data = r[:, :k]
    scores = np.log2(1./np.arange(1, k+1))
    pred_data = pred_data/scores
    pred_data = pred_data.sum(1)
    return np.sum(pred_data)


def NDCGatK_r(r, k):
    """
    Normalized Discounted Cumulative Gain
    rel_i = 1 or 0, so 2^{rel_i} - 1 = 1 or 0
    """
    pred_data = r[:, :k]
    max_r = np.sort(pred_data, axis=1)[:, ::-1]
    idcg = np.sum(max_r * 1./np.log2(np.arange(2, k + 2)), axis=1)
    dcg = pred_data*(1./np.log2(np.arange(2, k + 2)))
    ndcg = dcg/idcg
    ndcg[np.isnan(ndcg)] = 0.
    return np.sum(ndcg)


def getLabel(test_data, pred_data):
    r = []
    for i in range(len(test_data)):
        groundTrue = test_data[i]
        predictTopK = pred_data[i]
        pred = list(map(lambda x: x in groundTrue, predictTopK))
        pred = np.array(pred).astype("float")
        r.append(pred)
    return np.array(r).astype('float')

# ====================end Metrics=============================
# =========================================================
def NDCGatK(test_data, pred_data, k):
    """
    Normalized Discounted Cumulative Gain
    rel_i = 1 or 0, so 2^{rel_i} - 1 = 1 or 0
    NOTE implementation is slooooow
    """
    pred_rel = []
    idcg = []
    for i in range(len(test_data)):
        groundTrue = test_data[i]
        predictTopK = pred_data[i][:k]
        pred = list(map(lambda x: x in groundTrue, predictTopK))
        pred = np.array(pred).astype("float")
        pred_rel.append(pred)


        if len(groundTrue) < k:
            coeForIdcg = np.log2(np.arange(2, len(groundTrue)+2))
        else:
            coeForIdcg = np.log2(np.arange(2, k + 2))

        idcgi = np.sum(1./coeForIdcg)
        idcg.append(idcgi)
        # print(pred)

    pred_rel = np.array(pred_rel)
    idcg = np.array(idcg)
    coefficients = np.log2(np.arange(2, k+2))
    # print(coefficients.shape, pred_rel.shape)
    # print(coefficients)
    assert len(coefficients) == pred_rel.shape[-1]
    
    pred_rel = pred_rel/coefficients
    dcg = np.sum(pred_rel, axis=1)
    ndcg = dcg/idcg
    return np.mean(ndcg)



def recall_precisionATk(test_data, pred_data, k=5):
    """
    test_data should be a list? cause users may have different amount of pos items. shape (test_batch, k)
    pred_data : shape (test_batch, k) NOTE: pred_data should be pre-sorted
    k : top-k
    """
    assert len(test_data) == len(pred_data)
    right_items = 0
    recall_n    = 0
    precis_n    = len(test_data)*k
    for i in range(len(test_data)):
        groundTrue = test_data[i]
        predictTopK= pred_data[i][:k]
        bingo      = list(filter(lambda x: x in groundTrue, predictTopK))
        right_items+= len(bingo)
        recall_n   += len(groundTrue)
    return {'recall': right_items/recall_n, 'precision': right_items/precis_n}


def MRRatK(test_data, pred_data, k):
    """
    Mean Reciprocal Rank
    """
    MRR_n = len(test_data)
    scores = 0.
    for i in range(len(test_data)):
        groundTrue = test_data[i]
        prediction = pred_data[i]
        for j, item in enumerate(prediction):
            if j >= k:
                break
            if item in groundTrue:
                scores += 1/(j+1)
                break
            
    return scores/MRR_n