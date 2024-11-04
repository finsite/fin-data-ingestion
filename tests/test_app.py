from src.app import main

def test_main(capsys):
    main()
    captured = capsys.readouterr()
    assert captured.out == "Hello, GitHub Container Registry!\n"
