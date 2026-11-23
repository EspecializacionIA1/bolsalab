"use client";

import { useState } from "react";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { Notice } from "@/components/ui/Notice";
import { Option } from "@/components/ui/Option";
import { Progress } from "@/components/ui/Progress";

const options = [
  ["A", "Más que hoy"],
  ["B", "Lo mismo que hoy"],
  ["C", "Menos que hoy"],
  ["D", "No sé"],
];

export default function Home() {
  const [selected, setSelected] = useState("C");

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-10 px-4 py-12">
      <section className="flex flex-col gap-4">
        <Eyebrow>Botones</Eyebrow>
        <div className="flex flex-wrap gap-3">
          <Button>Siguiente →</Button>
          <Button variant="ghost">← Anterior</Button>
          <ButtonLink href="/" variant="ghost">
            Cómo funciona
          </ButtonLink>
          <Button disabled>Ver mi resultado</Button>
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between gap-4">
          <Eyebrow className="text-muted">Pregunta 11 de 13 · Lo que sabes</Eyebrow>
          <span className="font-mono text-xs text-muted">11 / 13</span>
        </div>
        <Progress current={11} total={13} label="Pregunta 11 de 13" />
      </section>

      <section className="flex flex-col gap-4">
        <h2 className="text-3xl leading-tight font-medium tracking-[-0.02em]">
          Tu cuenta paga 1 % al año y la inflación es de 2 % al año. Dentro de un año, ¿cuánto podrías comprar?
        </h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {options.map(([letter, label]) => (
            <Option
              key={letter}
              name="inflation"
              letter={letter}
              label={label}
              checked={selected === letter}
              onSelect={() => setSelected(letter)}
            />
          ))}
        </div>
      </section>

      <section className="grid gap-3 md:grid-cols-2">
        <Card className="flex flex-col gap-2">
          <Eyebrow>¿Por qué preguntamos esto?</Eyebrow>
          <p>Mide si conoces la inflación: si los precios suben más que tu dinero, compras menos.</p>
        </Card>
        <div className="flex flex-col gap-3">
          <Notice>No te pedimos nombre, correo ni documento, y no guardamos tus respuestas.</Notice>
          <Notice title="Toma este resultado con cuidado" tone="warning">
            Con personas de 60 años o más, el modelo acierta menos que con las demás.
          </Notice>
          <Notice title="No pudimos calcular tu resultado" tone="error">
            Puede ser tu conexión o nuestro servidor. Tus respuestas siguen aquí.
          </Notice>
        </div>
      </section>
    </main>
  );
}
