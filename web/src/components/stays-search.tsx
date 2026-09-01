'use client'

import { ChangeEvent, FormEvent, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { City, StayType } from '@/lib/types'
import { track } from '@/lib/analytics'

type Props = {
  cities: City[]
  initialCity?: string
  initialQuery?: string
  initialStayType?: StayType
}

export function StaysSearch({ cities, initialCity = '', initialQuery = '', initialStayType }: Props) {
  const router = useRouter()
  const [city, setCity] = useState(initialCity)
  const [query, setQuery] = useState(initialQuery)
  const [stayType, setStayType] = useState<StayType | ''>(initialStayType ?? '')

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const params = new URLSearchParams()
    if (city) params.set('city', city)
    if (query.trim()) params.set('q', query.trim())
    if (stayType) params.set('stay_type', stayType)
    track('stays_search', { city: city || 'all', stay_type: stayType || 'all' })
    router.push(`/stays?${params.toString()}`)
  }

  return <form className="stay-search" onSubmit={submit}>
    <label><span>City</span><select value={city} onChange={(e: ChangeEvent<HTMLSelectElement>) => setCity(e.target.value)}><option value="">All cities</option>{cities.map(item => <option value={item.name} key={item.name}>{item.name}</option>)}</select></label>
    <label className="stay-search-wide"><span>College, area, landmark or property</span><input value={query} onChange={(e: ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)} placeholder="JECRC, Sitapura, Medanta…" /></label>
    <fieldset><legend>Stay type</legend><div className="intent-row">
      {([['student','Student'],['corporate','Corporate'],['short_stay','Short stay']] as const).map(([value,label]) => <label className="intent" key={value}><input type="radio" name="stay_type" value={value} checked={stayType === value} onChange={() => setStayType(value)} /><span>{label}</span></label>)}
      <button type="button" className="intent-clear" onClick={() => setStayType('')}>Any</button>
    </div></fieldset>
    <button className="search-submit" type="submit">Find stays</button>
  </form>
}
