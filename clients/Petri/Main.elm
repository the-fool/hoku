module Petri.Main exposing (..)

import Html.Attributes
import Html.Events exposing (..)
import WebSocket
import Html exposing (..)
import Json.Decode exposing (Decoder, int, bool, decodeString, field, list, float)
import Json.Decode.Pipeline exposing (decode, required)
import Svg exposing (svg, circle, g)
import Svg.Keyed
import Svg.Attributes exposing (width, height, cx, cy, r, x, y, transform)
import AnimationFrame
import Time exposing (Time)


main =
    Html.program
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }



-- MODEL


type alias Bug =
    { pk : Int
    , x : Float
    , y : Float
    , dinging : Bool
    }


type alias Model =
    { message : String
    , bugs : List Bug
    }


init : ( Model, Cmd Msg )
init =
    ( Model
        ""
        []
    , Cmd.none
    )



-- UPDATE


bugDecoder : Decoder Bug
bugDecoder =
    decode Bug
        |> required "pk" int
        |> required "x" float
        |> required "y" float
        |> required "dinging" bool


msgDecoder =
    decodeString (field "agents" (list bugDecoder))


type Msg
    = NewMessage String
    | Paint Time


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NewMessage str ->
            ( { model | message = str }, Cmd.none )

        Paint t ->
            let
                newBugs =
                    case msgDecoder model.message of
                        Ok bugs ->
                            bugs

                        Err e ->
                            Debug.log "e" e |> always model.bugs
            in
                ( { model | bugs = newBugs }, Cmd.none )



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ WebSocket.listen "ws://127.0.0.1:7700" NewMessage
        , AnimationFrame.diffs Paint
        ]



-- VIEW


bugView : Bug -> ( String, Svg.Svg Msg )
bugView bug =
    ( toString bug.pk
    , g [ transform <| "translate(" ++ toString bug.x ++ " " ++ toString bug.y ++ ")" ]
        [ circle [ cx "0", cy "0", r "50" ] []
        ]
    )


view : Model -> Html Msg
view model =
    div []
        [ text <| toString <| List.length model.bugs
        , svg [ width "600", height "500" ]
            [ Svg.Keyed.node "g" [] <| List.map bugView model.bugs
            ]
        ]


viewMessage : String -> Html msg
viewMessage msg =
    div [] [ text msg ]
