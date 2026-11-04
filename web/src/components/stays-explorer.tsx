'use client'

import { FormEvent, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import styles from './stays-explorer.module.css'

const cities = ['Gurugram', 'Jaipur', 'Ahmedabad', 'Alibaug', 'Goa', 'Haridwar', 'Hyderabad', 'Karjat', 'Kasauli', 'Kota', 'Lonavala', 'Manali', 'Mumbai', 'Mussoorie', 'Nashik', 'Noida', 'Ooty', 'Panchgani', 'Pune', 'Udaipur']
const liveCities: Record<string, string> = { Gurugram: '/stays/gurugram', Jaipur: '/stays/jaipur' }

export function StaysExplorer() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [hint, setHint] = useState(cities[0])

  useEffect(() => {
    let cityIndex = 0
    let letterIndex = cities[0].length
    let deleting = true
    const timer = window.setInterval(() => {
      const city = cities[cityIndex]
      if (deleting) {
        letterIndex -= 1
        setHint(city.slice(0, Math.max(0, letterIndex)))
        if (letterIndex === 0) { deleting = false; cityIndex = (cityIndex + 1) % cities.length }
      } else {
        const next = cities[cityIndex]
        letterIndex += 1
        setHint(next.slice(0, letterIndex))
        if (letterIndex === next.length) deleting = true
      }
    }, 150)
    return () => window.clearInterval(timer)
  }, [])

  function visit(city: string) {
    setQuery(city)
    const route = liveCities[city]
    if (route) router.push(route)
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const matchingCity = cities.find(city => city.toLowerCase() === query.trim().toLowerCase())
    if (matchingCity && liveCities[matchingCity]) router.push(liveCities[matchingCity])
  }

  return <>
    <section className={styles.hero}>
      <div className={styles.stars} aria-hidden="true" /><span className={styles.shootingStar} aria-hidden="true" />
      <div className={styles.heroCopy}><span>FESTIVE CITY STAYS</span><h1>Plan your Diwali <em>stay beautifully.</em></h1><p>Thoughtfully located stays in Gurugram and Jaipur.</p></div>
      <form className={styles.search} onSubmit={submit} role="search"><span>Search for a property in</span><input aria-label="Search for a property" value={query} onChange={event => setQuery(event.target.value)} placeholder={hint} /><button type="submit" aria-label="Search stays">⌕</button></form>
    </section>
    <section className={styles.destinations} aria-labelledby="destination-title"><div><span>EXPLORE INDIA</span><h2 id="destination-title">Pick your destination.</h2></div><div className={styles.destinationGrid}>{cities.map((city, index) => <button type="button" key={city} aria-label={`Destination ${city}`} onClick={() => visit(city)}><i aria-hidden="true" data-icon={index % 6} /><b>{city}</b></button>)}</div></section>
  </>
}
