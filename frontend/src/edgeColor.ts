/** The photo's own background color (average of its top corners), so the tile behind a
 *  `object-fit: contain` image blends seamlessly whether the shot is on white or black. */
export function edgeColor(img: HTMLImageElement): string | null {
  try {
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = 16
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    if (!ctx) return null
    ctx.drawImage(img, 0, 0, 16, 16)
    const [a, b] = [ctx.getImageData(0, 0, 1, 1).data, ctx.getImageData(15, 0, 1, 1).data]
    return `rgb(${(a[0] + b[0]) >> 1} ${(a[1] + b[1]) >> 1} ${(a[2] + b[2]) >> 1})`
  } catch {
    return null // cross-origin or decode issue: keep the default tile color
  }
}
