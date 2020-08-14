# Stereonet

This program plots lines and planes on a stereonet and lets you analyse the data
neatly.

You can use the program by running `make run` or running `app.py` directly with
Python 3. `TestData.snet` contains some example data to play with -- open it
from Stereonet. Note that you need to select a group using the round radio
buttons in the list on the right before you can do most things!

There are built-in tests using Python's `unittest` module; run `make test` to
run them.

References I found useful when implementing this program were:

- Allmendinger, R. W., Cardozo, N. & Fisher, D. M.
  *Structural Geology Algorithms: Vectors and Tensors.*
  (Cambridge University Press, 2011).
  doi:[`10.1017/CBO9780511920202`][geo-algo].
- Cardozo, N. & Allmendinger, R. W.
  *Spherical projections with OSXStereonet.*
  Computers & Geosciences 51, 193–205 (2013).
  doi:[`10.1016/j.cageo.2012.07.021`][card-all].

[card-all]: https://dx.doi.org/10.1016/j.cageo.2012.07.021
[geo-algo]: https://dx.doi.org/10.1017/CBO9780511920202
