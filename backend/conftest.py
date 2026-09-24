# Empty on purpose: pytest adds this file's directory (backend/) to
# sys.path in rootless import mode, so `tests/*.py` can `import main`,
# `import rules`, etc. without a src-layout or installed package.
