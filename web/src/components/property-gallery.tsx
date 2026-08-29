export function PropertyGallery({ propertyName }: { propertyName: string }) {
  return <div className="property-gallery" aria-label={`${propertyName} gallery`}>
    <div className="gallery-main" role="img" aria-label={`${propertyName} approved photography pending`} />
    <div className="gallery-note"><strong>PROPERTY GALLERY</strong><span>Approved property photography will appear here when published by Livenza Admin.</span></div>
  </div>
}
