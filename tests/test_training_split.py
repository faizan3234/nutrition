import pytest
from training.split_by_group import split_rows

def test_groups_never_leak_between_splits():
    rows=[{'image_path':f'plate_{i}_angle_{j}.jpg','label':'dosa' if i%2 else 'idli','group_id':str(i)} for i in range(40) for j in range(3)]
    result=split_rows(rows)
    seen=[]
    for split,v in result.items():
        ids={r['group_id'] for r in v}
        assert len(ids)>=3
        seen.append(ids)
        assert len(v)%3==0
    assert not(seen[0]&seen[1] or seen[1]&seen[2] or seen[0]&seen[2])
    assert len([x for r in result.values() for x in r])==len(rows)
    assert split_rows(rows)==split_rows(rows)

def test_too_small_rejected():
    with pytest.raises(ValueError):split_rows([{'image_path':'a','label':'dosa','group_id':'1'}])
