module Main exposing (..)

import Html exposing (Html, program)
import Svg exposing (circle, line, svg, g, rect)
import Svg.Attributes exposing (..)
import Time exposing (Time, second, millisecond)


main =
    program { init = init, view = view, update = update, subscriptions = subs }


type alias NoteBank =
    { color : String
    , notes : List Bool
    }



-- MODEL


type alias Model =
    { step : Int
    , noteBanks : List NoteBank
    }



-- VIEW

steps = 16

view : Model -> Html Msg
view model =
    let
        angle =
            turns <| (\x -> x / steps) <| toFloat <| model.step

        handX =
            toString (50 + 40 * cos (angle))

        handY =
            toString (50 + 40 * sin (angle))
    in
        svg [ viewBox "0 0 100 100", width "800px", height "500px" ]
            [ circle [ cx "50", cy "50", r "45", fill "#0B79CE" ] []
            , g [ id "note-banks" ] (noteBanks model)
            , line [ x1 "50", y1 "50", x2 handX, y2 handY, stroke "#023963" ] []
            ]


noteBanks model =
    let
        toBank i noteBank =
            List.indexedMap
                (\j _ ->
                    rect
                        [ width "10"
                        , height "10"
                        , x << toString << (*) 11 <| i
                        , y << toString << (*) 11 <| j
                        ]
                        []
                )
                noteBank.notes
                |> g [ id noteBank.color, class "note-bank" ]
    in
        List.indexedMap toBank model.noteBanks



-- UPDATE


type Msg
    = Tick


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Tick ->
            ( { model | step = (model.step + 1) % steps }, Cmd.none )


init : ( Model, Cmd Msg )
init =
    ( { step = 0
      , noteBanks =
            [ "red", "blue", "green", "yellow" ]
                |> List.map (\x -> { color = x, notes = List.repeat 6 False })
      }
    , Cmd.none
    )


subs : Model -> Sub Msg
subs model =
    Time.every (250 * millisecond) (always Tick)
