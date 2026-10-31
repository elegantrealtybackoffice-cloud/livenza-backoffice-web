import Image from 'next/image'

export function PropertyGallery({ propertyName, photos = [], videos = [] }: { propertyName: string; photos?: string[]; videos?: string[] }) {
  if (!photos.length && !videos.length) return <div className="gallery-pending"><span>LIVENZA STAYS</span><strong>{propertyName}</strong><p>Property photography and video are being prepared. Contact our team for the latest details.</p></div>
  return <section className="property-gallery-wrap" aria-label={`${propertyName} gallery`}>
    <div className="property-gallery">
      {photos.map((photo, index) => <div className={`gallery-photo ${index === 0 ? 'gallery-photo-featured' : ''}`} key={photo}><Image src={photo} alt={`${propertyName} property photo ${index + 1}`} width={index === 0 ? 1100 : 520} height={index === 0 ? 700 : 390} priority={index === 0} /></div>)}
    </div>
    {videos.length > 0 && <div className="property-videos"><h2>Walk through the space.</h2><div className="property-video-grid">{videos.map((video, index) => <div className="property-video" key={video}><video controls preload="metadata" playsInline poster={photos[0]} aria-label={`${propertyName} video tour ${index + 1}`}><source src={video} type="video/mp4" />Your browser does not support video playback.</video><span>VIDEO TOUR {String(index + 1).padStart(2, '0')}</span></div>)}</div></div>}
  </section>
}
