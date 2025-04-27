{
  description = "Android CI Crawler";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      forAllSystems = f: nixpkgs.lib.genAttrs nixpkgs.lib.systems.flakeExposed (system: f system);
      pkgsFor = system: import nixpkgs { inherit system; };
    in
    {
      devShells = forAllSystems (system:
        let pkgs = pkgsFor system; in {
          default = pkgs.mkShell {
            packages = with pkgs; [
              sqlite-interactive
              (python313.withPackages (python-pkgs: with python-pkgs; [
                selenium
                undetected-chromedriver
                requests
              ]))
              undetected-chromedriver
              chromium
            ];
          };
        });
    };
}
