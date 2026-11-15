# -*- coding: utf-8 -*-
"""PyTorch 2.6.0 kaynağından kesitleri alır, 70 sütuna sığdırır ve
kırılmış sürümün AST'sinin orijinalle özdeş olduğunu doğrular."""
import ast, textwrap, sys
SRC = ("C:/Users/merty/AppData/Local/Programs/Python/Python312/"
       "Lib/site-packages/torch/nn/functional.py")
satirlar = open(SRC, encoding="utf-8").read().split("\n")

def al(a, b):
    return satirlar[a - 1:b]

def sar(orig, yeni):
    o = ast.dump(ast.parse("if True:\n" + "\n".join(orig)))
    n = ast.dump(ast.parse("if True:\n" + "\n".join(yeni)))
    return o == n

# A: scaled_dot_product_attention başvuru uygulaması (5731-5757)
A_o = al(5731, 5757)
A_n = ["        # Efficient implementation equivalent to the following:",
       "        def scaled_dot_product_attention(query, key, value,",
       "                attn_mask=None, dropout_p=0.0,",
       "                is_causal=False, scale=None,",
       "                enable_gqa=False) -> torch.Tensor:",
       "            L, S = query.size(-2), key.size(-2)",
       "            scale_factor = (1 / math.sqrt(query.size(-1))",
       "                            if scale is None else scale)",
       "            attn_bias = torch.zeros(L, S, dtype=query.dtype,",
       "                                    device=query.device)",
       "            if is_causal:",
       "                assert attn_mask is None",
       "                temp_mask = (torch.ones(L, S, dtype=torch.bool)",
       "                             .tril(diagonal=0))",
       "                attn_bias.masked_fill_(temp_mask.logical_not(),",
       "                                       float(\"-inf\"))",
       "                attn_bias.to(query.dtype)",
       "",
       "            if attn_mask is not None:",
       "                if attn_mask.dtype == torch.bool:",
       "                    attn_bias.masked_fill_(attn_mask.logical_not(),",
       "                                           float(\"-inf\"))",
       "                else:",
       "                    attn_bias = attn_mask + attn_bias",
       "",
       "            if enable_gqa:",
       "                key = key.repeat_interleave(query.size(-3) //",
       "                                            key.size(-3), -3)",
       "                value = value.repeat_interleave(query.size(-3) //",
       "                                                value.size(-3), -3)",
       "",
       "            attn_weight = query @ key.transpose(-2, -1) * scale_factor",
       "            attn_weight += attn_bias",
       "            attn_weight = torch.softmax(attn_weight, dim=-1)",
       "            attn_weight = torch.dropout(attn_weight, dropout_p,",
       "                                        train=True)",
       "            return attn_weight @ value"]
# B: çok başlı attention, Q/K/V paketli projeksiyon (6226-6230)
B_o = al(6226, 6230)
B_n = ["    if not use_separate_proj_weight:",
       "        assert (",
       "            in_proj_weight is not None",
       "        ), (\"use_separate_proj_weight is False but \"",
       "            \"in_proj_weight is None\")",
       "        q, k, v = _in_projection_packed(query, key, value,",
       "                                        in_proj_weight, in_proj_bias)",
       "    # else dalı bu kesitte atlandı"]
# C: başlara bölme (reshape) (6294-6298)
C_o = al(6294, 6298)
C_n = ["    # reshape q, k, v for multihead attention and make them",
       "    # batch first",
       "    q = q.view(tgt_len, bsz * num_heads, head_dim).transpose(0, 1)",
       "    if static_k is None:",
       "        k = k.view(k.shape[0], bsz * num_heads,",
       "                   head_dim).transpose(0, 1)",
       "    # else dalı bu kesitte atlandı"]
# D: başları birleştirme ve çıkış projeksiyonu (6378-6384)
D_o = al(6378, 6384)
D_n = ["        attn_output = torch.bmm(attn_output_weights, v)",
       "",
       "        attn_output = (",
       "            attn_output.transpose(0, 1).contiguous()",
       "            .view(tgt_len * bsz, embed_dim)",
       "        )",
       "        attn_output = linear(attn_output, out_proj_weight,",
       "                             out_proj_bias)",
       "        attn_output = attn_output.view(tgt_len, bsz,",
       "                                       attn_output.size(1))"]
# D'de else/if satırları yok; orijinal parçayı kırpılmamış hâliyle
# karşılaştırmak için yalnızca bmm-tuple-linear-view dizisini alıyoruz.
sonuc = {}
for ad, o, n in [("A", A_o, A_n), ("B", B_o, B_n), ("C", C_o, C_n),
                 ("D", D_o, D_n)]:
    ok = sar([x for x in o if x.strip() and not x.strip().startswith("#")],
             [x for x in n if x.strip() and not x.strip().startswith("#")])
    sonuc[ad] = ok
    print(ad, "AST ozdes:", ok)
    if ad in "ABCD":
        sut = max(len(x) for x in n)
        print(ad, "en uzun satir:", sut)
        dd = textwrap.dedent("\n".join(n))
        open("kk_%s.py" % ad, "w", encoding="utf-8").write(dd + "\n")
