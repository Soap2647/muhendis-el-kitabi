if not use_separate_proj_weight:
    assert (
        in_proj_weight is not None
    ), ("use_separate_proj_weight is False but "
        "in_proj_weight is None")
    q, k, v = _in_projection_packed(query, key, value,
                                    in_proj_weight, in_proj_bias)
# else dalı bu kesitte atlandı
