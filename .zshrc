iikanji() {
  # Paths
  app="$HOME/Desktop/Coding/ii-kanji/ii-kanji-macOS-arm64"
  cfg="$HOME/Desktop/Coding/ii-kanji/config.txt"
  scores_dir="$HOME/Desktop/Coding/ii-kanji/scores"

  # No args → run app
  if [ $# -eq 0 ]; then
    "$app"
    return
  fi

  # Enforce exactly one of: -c  OR  -rm <name>
  if [ "$1" = "-c" ] && [ $# -eq 1 ]; then
    nano "$cfg"
    return
  fi

  if [ "$1" = "-rm" ] && [ $# -eq 2 ]; then
    name="$2"
    file="$scores_dir/$name"

    if [ ! -e "$file" ]; then
      echo "Not found: $file"
      return 1
    fi

    printf "Are you sure you want to delete %s's? (y/n) " "$name"
    read -r confirm
    case "$confirm" in
      [yY]|[yY][eE][sS])
        # Use -- so a weird name starting with '-' isn't treated as an option
        rm -- "$file" && echo "Deleted: $file"
        ;;
      *)
        echo "Cancelled."
        ;;
    esac
    return
  fi

  # If we get here, the usage is wrong or options conflict
  echo "Usage:"
  echo "  iikanji           # run app"
  echo "  iikanji -c        # edit config"
  echo "  iikanji -rm <name># delete scores/<name> (with confirm)"
  echo "Note: -c and -rm cannot be used together."
  return 1
}
