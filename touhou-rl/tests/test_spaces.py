from touhou_rl.common.spaces import MOVES, build_action_table


def test_default_action_table_size():
    table = build_action_table(include_focus=True, include_bomb=False)
    # 9 向移动 × {低速关, 低速开} = 18
    assert len(table) == len(MOVES) * 2 == 18


def test_no_focus():
    table = build_action_table(include_focus=False, include_bomb=False)
    assert len(table) == len(MOVES)
    assert all(not b.focus for b in table)


def test_with_bomb():
    table = build_action_table(include_focus=True, include_bomb=True)
    assert len(table) == 18 + 1
    assert any(b.bomb for b in table)


def test_always_shoot():
    table = build_action_table(always_shoot=True)
    # 除 Bomb 专用动作外，射击均常按
    assert all(b.shoot for b in table)


def test_idle_action_present():
    table = build_action_table()
    assert any(b.dx == 0 and b.dy == 0 and not b.focus for b in table)
