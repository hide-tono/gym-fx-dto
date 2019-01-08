https://github.com/openai/gym/tree/master/gym/envs#how-to-create-new-environments-for-gym を参考に作成。

## インストール方法


```python
cd gym-fx-dto
pip install -e .
```

or


```python
cd gym-fx-dto
python setup.py build
python setup.py install
```

## 利用時のインポート

test/test.py 参照

```python
from gym_fx_dto.envs import FxDtoEnv
```

## (メモ)conda仮想環境の変更

```python
source activate py36
```