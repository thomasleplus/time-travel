-- Records which version of the source a copy of the book was built from: the git commit, the
-- tags on it, if any, and whether there were uncommitted changes. It sets the revision
-- metadata field, which the EPUB template shows on the title page, and for the PDF the
-- \bookrevision command, which the copyright page shows (styles/copyright-page.tex).
-- Outside a git repository, it does nothing.

-- luacheck: read globals pandoc quarto

local function git(args)
  local ok, output = pcall(pandoc.pipe, "git", args, "")
  if ok then
    return (output:gsub("%s+$", ""))
  end
end

local function revision()
  local commit = git({ "rev-parse", "--short", "HEAD" })
  if not commit or commit == "" then
    return nil
  end
  -- diff-index exits with an error when tracked files differ from the commit
  if not git({ "diff-index", "--quiet", "HEAD", "--" }) then
    commit = commit .. " (modified)"
  end
  local tags = git({ "tag", "--points-at", "HEAD" }) or ""
  if tags == "" then
    return "Revision " .. commit
  end
  return "Version " .. tags:gsub("\n", ", ") .. ", revision " .. commit
end

return {
  {
    Meta = function(meta)
      local text = revision()
      if not text then
        return nil
      end
      meta.revision = text
      if quarto.doc.is_format("latex") then
        -- Tag names may contain characters that LaTeX treats as special
        local latex = text:gsub("[_&%%#$]", "\\%0")
        quarto.doc.include_text("in-header", "\\newcommand{\\bookrevision}{" .. latex .. "}")
      end
      return meta
    end,
  },
}
