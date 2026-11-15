    if topdown:
        yield top, dirs, nondirs

        # Recurse into sub-directories
        islink, join = path.islink, path.join
        for dirname in dirs:
            new_path = join(top, dirname)
            # Issue #23605: os.path.islink() is used instead of
            # caching
            # entry.is_symlink() result during the loop on
            # os.scandir() because
            # the caller can replace the directory entry during the
            # "yield"
            # above.
            if followlinks or not islink(new_path):
                yield from _walk(new_path, topdown, onerror,
                                  followlinks)
