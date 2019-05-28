(function () {
  /* Checks localstorage for previously configured style options and
   * applies them if found.
   */
  var perf = window.performance;
  if (perf && perf.navigation.type == perf.navigation.TYPE_RELOAD) {
    var style = document.createElement("style");
    style.textContent = "#below-the-fold {display: block;}";
    document.head.appendChild(style);
  }

  var cl = document.body.classList;

  var stored_font = localStorage.getItem("litprog_font")
  if (stored_font != null) {
    cl.remove("font-serif");
    cl.remove("font-sans");
    cl.remove("font-slab");
    cl.add("font-" + stored_font);
  }

  var stored_theme = localStorage.getItem("litprog_theme")
  var use_dark_theme = (
    stored_theme !== null && stored_theme == "dark"
    || matchMedia('(light-level: dim)').matches
    || matchMedia('(prefers-color-scheme: dark)').matches
  );
  if (use_dark_theme) {
    cl.add("dark");
  } else {
    cl.add("light");
  }
})();