def test_main_invokes_click_app(monkeypatch):
    import polyzone.__main__ as main_module

    called = []
    monkeypatch.setattr(main_module, "app", lambda: called.append(True))

    main_module.main()
    assert called == [True]
