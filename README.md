# nomz

tiny daemon for window swallowing on sway

## Usage

Install the package from git:

```sh
$ pip install --user git+https://github.com/dzshn/nomz
```

Then run it with:

```sh
$ nomz [app id…] # e.g. `nomz kitty` or `nomz Alacritty`
```

Or add it to your sway config:

```
exec nomz [app id…]
```
