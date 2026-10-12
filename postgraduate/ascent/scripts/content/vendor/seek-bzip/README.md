seek-bzip 2.0.0 (MIT, https://github.com/cscott/seek-bzip), vendored so the content scripts can read
Tatoeba .bz2 exports without a new npm dependency. Only the require paths, the package.json lookup and the deprecated `new Buffer(n)` calls (now `Buffer.alloc(n)`) were changed.
