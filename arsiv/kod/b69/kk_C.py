# reshape q, k, v for multihead attention and make them
# batch first
q = q.view(tgt_len, bsz * num_heads, head_dim).transpose(0, 1)
if static_k is None:
    k = k.view(k.shape[0], bsz * num_heads,
               head_dim).transpose(0, 1)
# else dalı bu kesitte atlandı
