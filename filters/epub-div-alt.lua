-- Quarto copies a figure's fig-alt onto the div that wraps it as well as onto the image.
-- alt is not a valid div attribute, which EPUBCheck reports as an error (RSC-005).
-- The image keeps its alt text.
return {
  {
    Div = function(div)
      if div.attributes.alt then
        div.attributes.alt = nil
        return div
      end
    end,
  },
}
