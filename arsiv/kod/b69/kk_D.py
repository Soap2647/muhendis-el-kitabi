attn_output = torch.bmm(attn_output_weights, v)

attn_output = (
    attn_output.transpose(0, 1).contiguous()
    .view(tgt_len * bsz, embed_dim)
)
attn_output = linear(attn_output, out_proj_weight,
                     out_proj_bias)
attn_output = attn_output.view(tgt_len, bsz,
                               attn_output.size(1))
