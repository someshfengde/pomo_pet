class PomoPet < Formula
  desc "Pomodoro timer with animated desktop pets"
  homepage "https://github.com/someshfengde/pomo_pet"
  url "https://github.com/someshfengde/pomo_pet/archive/refs/heads/main.tar.gz"
  sha256 "0e0334148f148823e53419e4fa7ba94f5ee4534a053dc25faabfeee54770d1ec"
  license "MIT"
  version "1.2.16"

  depends_on "python@3.13"
  depends_on "uv"

  def install
    # Create a virtualenv using uv
    system "uv", "venv", libexec/"venv", "--python", "python3.13"

    # Install the package into the venv
    system "uv", "pip", "install", "--python", libexec/"venv/bin/python",
           "--no-cache", buildpath

    # Create wrapper script
    (bin/"pomo-pet").write <<~SH
      #!/bin/bash
      export VIRTUAL_ENV="#{libexec}/venv"
      export PATH="#{libexec}/venv/bin:$PATH"
      exec python3 -m src "$@"
    SH
    (bin/"pomo-pet").chmod 0755
  end

  test do
    assert_match "pomo-pet, version", shell_output("#{bin}/pomo-pet --version")
  end
end
