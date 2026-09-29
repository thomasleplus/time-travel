-- Quarto copies a figure's fig-alt onto the div that wraps it as well as onto the image.
-- alt is not a valid div attribute, which EPUBCheck reports as an error (RSC-005).
-- It copies aria-describedby too, which would link the figure's description a second time.
-- The image keeps both.
return {
  {
    Div = function(div)
      if div.attributes.alt then
        div.attributes.alt = nil
        div.attributes["aria-describedby"] = nil
        return div
      end
    end,
  },
}
