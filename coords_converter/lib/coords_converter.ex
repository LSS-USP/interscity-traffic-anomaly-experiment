defmodule CoordsConverter do
  import SweetXml

  def run_convertions(origin_path, dest_path) do
    st = File.stream!(origin_path)

    ids = st |> xpath(~x"//nodes/node/@id"l)
    xs = st |> xpath(~x"//nodes/node/@x"l)
    ys = st |> xpath(~x"//nodes/node/@y"l)

    File.open(dest_path, [:write], fn(file) ->
      [ids, xs, ys]
      |> Enum.zip
      |> Enum.chunk_every(2)
      |> Enum.each(fn coord ->
        endpoint = "https://epsg.io/trans?data="
        ";"<>parameters = Enum.reduce(coord, "", fn({id, x, y}, acc) -> acc<>";#{x},#{y}" end)

        response =
          endpoint <> parameters <> "&s_srs=32719&t_srs=4326"
          |> HTTPoison.get!

          {:ok, payload} = Poison.decode(response.body)

        Enum.each(payload, fn (coord) ->
          item = "<node id=\"#{id}\" x=\"#{x}\" y=\"#{y}\" lat=\"#{payload["x"]}\" lon=\"#{payload["y"]}\" />"
      end)
        
        # ({id, x, y}) ->
        #
        # item = "<node id=\"#{id}\" x=\"#{x}\" y=\"#{y}\" lat=\"#{payload["x"]}\" lon=\"#{payload["y"]}\" />"
        # IO.puts(file, item)
        # IO.puts "+"

    end)
  end
end
