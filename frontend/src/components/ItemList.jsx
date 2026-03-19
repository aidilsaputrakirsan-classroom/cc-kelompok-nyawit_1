import { useEffect, useState } from "react"
import ItemCard from "./ItemCard"

function ItemList({ items, onEdit, onDelete, loading, deleteLoadingId = null }) {
  const spinnerFrames = ["|", "/", "-", "\\"]
  const [spinnerIndex, setSpinnerIndex] = useState(0)

  useEffect(() => {
    if (!loading) return
    const timer = setInterval(() => {
      setSpinnerIndex((prev) => (prev + 1) % spinnerFrames.length)
    }, 120)

    return () => clearInterval(timer)
  }, [loading])

  if (loading) {
    return (
      <div style={styles.message}>
        <span style={styles.spinner}>{spinnerFrames[spinnerIndex]}</span>
        <span>Memuat data...</span>
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div style={styles.empty}>
        <p style={styles.emptyIcon}>📭</p>
        <p style={styles.emptyText}>Belum ada item.</p>
        <p style={styles.emptyHint}>
          Gunakan form di atas untuk menambahkan item pertama.
        </p>
      </div>
    )
  }

  return (
    <div style={styles.grid}>
      {items.map((item) => (
        <ItemCard
          key={item.id}
          item={item}
          onEdit={onEdit}
          onDelete={onDelete}
          isDeleting={deleteLoadingId === item.id}
        />
      ))}
    </div>
  )
}

const styles = {
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
    gap: "1rem",
  },
  message: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "0.6rem",
    color: "#888",
    padding: "2rem",
    fontSize: "1.1rem",
  },
  spinner: {
    display: "inline-block",
    width: "14px",
    textAlign: "center",
    fontWeight: "bold",
    color: "#1F4E79",
  },
  empty: {
    textAlign: "center",
    padding: "3rem",
    backgroundColor: "#f8f9fa",
    borderRadius: "12px",
    border: "2px dashed #ddd",
  },
  emptyIcon: {
    fontSize: "3rem",
    margin: "0 0 0.5rem 0",
  },
  emptyText: {
    fontSize: "1.1rem",
    color: "#555",
    margin: "0 0 0.25rem 0",
  },
  emptyHint: {
    fontSize: "0.9rem",
    color: "#888",
    margin: 0,
  },
}

export default ItemList