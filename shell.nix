{
  pkgs ? import <nixpkgs> { },
}:
pkgs.mkShell {
  packages = with pkgs; [
    python314

    uv
    pyright
    ruff

    pre-commit

    ollama
  ];
}
