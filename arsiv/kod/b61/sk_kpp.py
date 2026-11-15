    if n_local_trials is None:
        # This is what Arthur/Vassilvitskii tried, but did not report
        # specific results for other than mentioning in the conclusion
        # that it helped.
        n_local_trials = 2 + int(np.log(n_clusters))

    # Pick first center randomly and track index of point
    center_id = random_state.choice(
        n_samples, p=sample_weight / sample_weight.sum())
    indices = np.full(n_clusters, -1, dtype=int)
    if sp.issparse(X):
        centers[0] = X[[center_id]].toarray()
    else:
        centers[0] = X[center_id]
    indices[0] = center_id

    # Initialize list of closest distances and calculate
    # current potential
    closest_dist_sq = _euclidean_distances(
        centers[0, np.newaxis], X, Y_norm_squared=x_squared_norms,
        squared=True
    )
    current_pot = closest_dist_sq @ sample_weight

    # Pick the remaining n_clusters-1 points
    for c in range(1, n_clusters):
        # Choose center candidates by sampling with probability
        # proportional
        # to the squared distance to the closest existing center
        rand_vals = (
            random_state.uniform(size=n_local_trials) * current_pot)
        candidate_ids = np.searchsorted(
            np.cumsum(sample_weight * closest_dist_sq), rand_vals
        )
        # XXX: numerical imprecision can result in a candidate_id
        # out of range
        np.clip(
            candidate_ids, None, closest_dist_sq.size - 1,
            out=candidate_ids)

        # Compute distances to center candidates
        distance_to_candidates = _euclidean_distances(
            X[candidate_ids], X, Y_norm_squared=x_squared_norms,
            squared=True
        )

        # update closest distances squared and potential for each
        # candidate
        np.minimum(
            closest_dist_sq, distance_to_candidates,
            out=distance_to_candidates)
        candidates_pot = distance_to_candidates @ (
            sample_weight.reshape(-1, 1))

        # Decide which candidate is the best
        best_candidate = np.argmin(candidates_pot)
        current_pot = candidates_pot[best_candidate]
        closest_dist_sq = distance_to_candidates[best_candidate]
        best_candidate = candidate_ids[best_candidate]

        # Permanently add best center candidate found in local tries
        if sp.issparse(X):
            centers[c] = X[[best_candidate]].toarray()
        else:
            centers[c] = X[best_candidate]
        indices[c] = best_candidate

    return centers, indices
