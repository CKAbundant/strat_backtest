def test_fn():
    a = [1, 2]

    x, y, *rest = a

    print(f"\n\n{x=}")
    print(f"{y=}")
    print(f"{rest=}\n")
