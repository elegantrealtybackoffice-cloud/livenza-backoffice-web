export type CuratedStay = {
  slug: string
  name: string
  sector: number
  landmark?: string
  photos: string[]
  videos: string[]
}

function media(slug: string, photoCount: number) {
  return photoCount ? [
    `/stays/${slug}/cover.webp`,
    ...Array.from({ length: photoCount - 1 }, (_, index) => `/stays/${slug}/${String(index + 1).padStart(2, '0')}.webp`),
  ] : []
}

export const curatedStays: CuratedStay[] = [
  { slug: 'the-sienna', name: 'The Sienna', sector: 38, landmark: 'Near Medanta', photos: media('the-sienna', 5), videos: [1, 2, 3].map(n => `/stays/the-sienna/video-0${n}.mp4`) },
  { slug: 'the-azure', name: 'The Azure', sector: 38, photos: [], videos: [] },
  { slug: 'g38-getaway', name: 'G 38 Getaway', sector: 38, landmark: 'Near Kutiz Skin Care Clinic', photos: media('g38-getaway', 9), videos: [] },
  { slug: 'the-elara', name: 'The Elara', sector: 51, photos: media('the-elara', 8), videos: [] },
  { slug: 'the-maralia', name: 'The Maralia', sector: 52, photos: [], videos: [] },
  { slug: 'the-avelia', name: 'The Avelia', sector: 51, photos: [], videos: [] },
]

export function getCuratedStay(slug: string): CuratedStay | undefined {
  return curatedStays.find(stay => stay.slug === slug)
}

export function whatsappHref(name?: string): string {
  const message = name ? `Hello Livenza Stays, I would like to enquire about ${name}.` : 'Hello Livenza Stays, I would like to enquire about a stay.'
  return `https://wa.me/917688845555?text=${encodeURIComponent(message)}`
}
